import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import sqlparse
from .auth import router as auth_router, allowed_origins

from .database import engine, get_db, SessionLocal
from .models import QueryHistory
from .schemas import GenerateRequest, ExecuteRequest, GenerateResponse, CandidateResponse
from .seed import seed_db
from .agents.prompt_processing import PromptProcessingAgent
from .agents.schema_understanding import SchemaUnderstandingAgent
from .agents.query_generation import QueryGenerationAgent
from .agents.offline_query import QueryRequestError
from .agents.query_explanation import QueryExplanationAgent
from .agents.query_impact import QueryImpactAnalyzer
from .agents.query_validation import QueryValidationAgent
from .agents.query_execution import QueryExecutionAgent

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

app = FastAPI(title="QueryGenie")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.include_router(auth_router)
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{os.getenv('RATE_LIMIT_PER_MINUTE', '10')}/minute"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please wait a minute and try again."})


@app.on_event("startup")
def startup():
    ensure_demo_ready()


schema_agent = SchemaUnderstandingAgent(engine)
prompt_agent = PromptProcessingAgent()
explanation_agent = QueryExplanationAgent()
impact_agent = QueryImpactAnalyzer(SessionLocal)
execution_agent = QueryExecutionAgent(engine, simulate_writes_only=os.getenv("SIMULATE_WRITES_ONLY", "True").lower() == "true")


@lru_cache(maxsize=1)
def get_schema_snapshot():
    return schema_agent.schema_map


def ensure_demo_ready():
    seed_db()
    schema_agent.refresh()


def _sanitize(value: str) -> str:
    # React renders these values as text; preserve SQL operators and literals.
    return value


def _log_history(db: Session, nl: str, sql: str, chosen: str, rows_affected, rows_returned, status: str, risk: str | None):
    record = QueryHistory(
        nl_input=_sanitize(nl),
        sql_generated=_sanitize(sql),
        query_chosen=_sanitize(chosen),
        rows_affected=rows_affected,
        rows_returned=rows_returned,
        execution_status=status,
        risk_warning=_sanitize(risk) if risk else None,
    )
    db.add(record)
    db.commit()


@app.get("/schema")
@limiter.limit("10/minute")
def schema(request: Request):
    ensure_demo_ready()
    return {table: meta for table, meta in schema_agent.schema_map.items() if table != 'QueryHistory'}


@app.get("/history")
def history(db: Session = Depends(get_db)):
    rows = db.query(QueryHistory).order_by(QueryHistory.timestamp.desc()).all()
    return [{"timestamp": r.timestamp, "nl_input": r.nl_input, "sql_generated": r.sql_generated, "query_chosen": r.query_chosen, "rows_affected": r.rows_affected, "rows_returned": r.rows_returned, "execution_status": r.execution_status, "risk_warning": r.risk_warning} for r in rows]


@app.get('/generation-status')
def generation_status():
    provider = os.getenv('LLM_PROVIDER', 'ANTHROPIC').upper()
    enabled = (provider == 'ANTHROPIC' and bool(os.getenv('ANTHROPIC_API_KEY'))) or (provider == 'GOOGLE' and bool(os.getenv('GOOGLE_API_KEY')))
    return {'mode': 'ai' if enabled else 'local', 'message': 'AI mode configured. Queries are checked against your database schema.' if enabled else 'Local mode: common requests are supported. Broader English requests require an AI API key in backend/.env.'}


@app.post("/generate")
@limiter.limit("10/minute")
def generate(payload: GenerateRequest, request: Request, db: Session = Depends(get_db)):
    ensure_demo_ready()
    if len(payload.nl_query) > 500:
        raise HTTPException(status_code=400, detail="NL input must be 500 characters or fewer.")
    normalized = prompt_agent.normalize(payload.nl_query)
    intent = prompt_agent.classify_intent(normalized)
    schema = {table: meta for table, meta in schema_agent.refresh().items() if table != 'QueryHistory'}
    try:
        generator = QueryGenerationAgent(schema)
        raw_candidates = generator.generate(payload.nl_query, intent)
    except QueryRequestError as exc:
        raise HTTPException(status_code=exc.status_code, detail={'code': exc.code, 'message': str(exc)}) from None
    candidates = []
    for cand in raw_candidates:
        validation = QueryValidationAgent(schema).validate(cand["sql"])
        explanation = explanation_agent.explain(cand["sql"])
        impact = impact_agent.estimate(cand["sql"])
        risk_warning = None
        if not validation["valid"] or impact["risky"] or any(k in cand["sql"].lower() for k in ["update", "delete"]):
            risk_warning = "This query may affect many rows or needs confirmation."
        candidates.append(CandidateResponse(
            sql=cand["sql"],
            explanation=explanation,
            tables_involved=explanation["tables_involved"],
            columns_involved=explanation["columns_involved"],
            impact_estimate=impact,
            optimization_suggestion=validation["optimized_alternative"],
            risk_warning=risk_warning,
            requires_confirmation=cand["sql"].lower().startswith(("update", "delete", "insert")),
        ).model_dump())
    if candidates:
        _log_history(db, payload.nl_query, candidates[0]["sql"], candidates[0]["sql"], candidates[0]["impact_estimate"].get("estimated_rows"), None, "generated", candidates[0].get("risk_warning"))
    return {"candidates": candidates}


@app.post("/execute")
@limiter.limit("10/minute")
def execute(payload: ExecuteRequest, request: Request, db: Session = Depends(get_db)):
    ensure_demo_ready()
    sql = payload.sql.strip()
    lowered = sql.lower()
    current_schema = {table: meta for table, meta in schema_agent.schema_map.items() if table != 'QueryHistory'}
    if not QueryGenerationAgent(current_schema, llm_client=object())._validate_sql(sql):
        raise HTTPException(status_code=400, detail='Invalid or unsafe SQL. Use one valid statement with existing tables/columns; UPDATE and DELETE require WHERE.')
    operation = sqlparse.parse(sql)[0].get_type()
    if len(sql) > 5000:
        raise HTTPException(status_code=400, detail="SQL payload too large.")
    if ";" in sql.rstrip(";") and sql.rstrip(";").count(";") > 0:
        raise HTTPException(status_code=400, detail="Multiple SQL statements are not allowed.")
    if operation in {'UPDATE', 'DELETE', 'INSERT'} and os.getenv("SIMULATE_WRITES_ONLY", "True").lower() == "true":
        impact = impact_agent.estimate(sql)
        rows_affected = impact.get("estimated_rows")
        _log_history(db, "", sql, sql, rows_affected, 0, "simulated", "Write simulation only.")
        return {"success": True, "rows": [], "rows_affected": rows_affected, "error": None, "simulated": True}
    try:
        result = execution_agent.execute(sql)
    except SQLAlchemyError:
        raise HTTPException(status_code=400, detail='The query could not be executed. Check its values and database constraints.') from None
    rows_returned = len(result["rows"]) if result["rows"] else 0
    _log_history(db, "", sql, sql, result["rows_affected"], rows_returned, "executed", None)
    return result
