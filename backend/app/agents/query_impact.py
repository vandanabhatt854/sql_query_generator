import re
import sqlparse
from sqlalchemy import text


class QueryImpactAnalyzer:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    def _table_from_sql(self, sql: str):
        m = re.search(r'\bfrom\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)', sql, flags=re.I)
        if m:
            return m.group(1)
        m = re.search(r'\bupdate\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)', sql, flags=re.I)
        if m:
            return m.group(1)
        return None

    def estimate(self, sql: str) -> dict:
        lower = sql.lower()
        session = self.db_session_factory()
        try:
            table = self._table_from_sql(sql)
            if sqlparse.parse(sql)[0].get_type() == 'SELECT':
                count_sql = f"SELECT COUNT(*) FROM ({sql.rstrip(';')}) AS q"
                rows = session.execute(text(count_sql)).scalar_one()
                return {"estimated_rows": int(rows), "method": "count-subquery", "risky": int(rows) > 100}
            if lower.startswith(("update", "delete")) and "where" in lower and table:
                where_clause = next(str(token) for token in sqlparse.parse(sql)[0].tokens if isinstance(token, sqlparse.sql.Where))
                count_sql = f'SELECT COUNT(*) FROM "{table}" {where_clause}'
                rows = session.execute(text(count_sql)).scalar_one()
                return {"estimated_rows": int(rows), "method": "where-count", "risky": int(rows) > 100}
            return {"estimated_rows": None, "method": "unknown", "risky": True}
        finally:
            session.close()
