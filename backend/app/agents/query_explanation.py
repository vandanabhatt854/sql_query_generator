import re


class QueryExplanationAgent:
    def explain(self, sql: str) -> dict:
        lowered = sql.lower()
        clauses = []
        for clause in ["join", "where", "group by", "order by", "limit", "having", "set"]:
            if clause in lowered:
                clauses.append(clause.upper())
        tables = re.findall(r"\bfrom\s+([A-Za-z_][A-Za-z0-9_]*)|\bjoin\s+([A-Za-z_][A-Za-z0-9_]*)|\bupdate\s+([A-Za-z_][A-Za-z0-9_]*)|\binsert\s+into\s+([A-Za-z_][A-Za-z0-9_]*)", lowered)
        flat_tables = sorted({t for group in tables for t in group if t})
        columns = sorted(set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|>|<|like|\)|,)", sql, flags=re.I)))
        return {
            "summary": "This query retrieves or modifies data based on the filters and clauses in the statement.",
            "clauses_used": clauses,
            "tables_involved": flat_tables,
            "columns_involved": columns,
        }

