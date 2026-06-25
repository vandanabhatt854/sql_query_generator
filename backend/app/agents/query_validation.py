import re
import sqlparse


class QueryValidationAgent:
    def __init__(self, schema_map, indexed_columns=None):
        self.schema_map = schema_map
        self.indexed_columns = indexed_columns or {"Employee": ["id", "department_id", "salary"], "Students": ["id", "cgpa"]}

    def validate(self, sql: str) -> dict:
        issues = []
        statements = sqlparse.parse(sql)
        if len(statements) != 1:
            issues.append("Only a single SQL statement is allowed.")
        if ";" in sql.strip().rstrip(";"):
            issues.append("Multiple statements are not allowed.")
        lowered = sql.lower()
        if "--" in sql or "/*" in sql or "*/" in sql:
            issues.append("SQL comments are blocked.")
        if any(bad in lowered for bad in ["drop", "truncate", "alter", "grant", "revoke", "attach", "exec"]):
            issues.append("Dangerous SQL keywords are blocked.")
        if re.search(r"select\s+\*", lowered):
            issues.append("SELECT * can be inefficient on wide tables.")
        if lowered.startswith(("update", "delete")) and "where" not in lowered:
            issues.append("UPDATE/DELETE without a WHERE clause is blocked.")
        optimized = None
        if issues:
            optimized = "Add explicit columns, filters, and LIMIT where appropriate."
        return {"valid": not issues, "issues": issues, "optimized_alternative": optimized}
