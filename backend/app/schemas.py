from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    nl_query: str = Field(max_length=500)


class ExecuteRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=5000)


class CandidateResponse(BaseModel):
    sql: str
    explanation: Dict[str, Any]
    tables_involved: List[str]
    columns_involved: List[str]
    impact_estimate: Dict[str, Any]
    optimization_suggestion: Optional[str] = None
    risk_warning: Optional[str] = None
    requires_confirmation: bool = False


class GenerateResponse(BaseModel):
    candidates: List[CandidateResponse]

