import re
import sqlparse
from sqlalchemy import text


class QueryExecutionAgent:
    def __init__(self, engine, simulate_writes_only=True):
        self.engine = engine
        self.simulate_writes_only = simulate_writes_only

    def execute(self, sql: str):
        lower = sql.lower().strip()
        with self.engine.begin() as conn:
            if sqlparse.parse(sql)[0].get_type() == 'SELECT':
                res = conn.execute(text(sql))
                rows = [dict(r._mapping) for r in res.fetchall()]
                return {"success": True, "rows": rows, "rows_affected": 0, "error": None}
            if self.simulate_writes_only:
                return {"success": True, "rows": [], "rows_affected": 0, "error": None}
            res = conn.execute(text(sql))
            return {"success": True, "rows": [], "rows_affected": res.rowcount, "error": None}

