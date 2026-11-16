import re
from typing import Dict, List


class QueryExplanationAgent:
    def _find_tables(self, sql: str) -> List[str]:
        lowered = sql.lower()
        tables = []
        for pattern in [r'\bfrom\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)', r'\bjoin\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)', r'\bupdate\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)', r'\binsert\s+into\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)']:
            tables.extend(re.findall(pattern, lowered, flags=re.I))
        seen = []
        for table in tables:
            if table and table not in seen:
                seen.append(table)
        return seen

    def _find_columns(self, sql: str) -> List[str]:
        tokens = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", sql)
        sql_lower = sql.lower()
        candidates = []
        keywords = {"select", "from", "where", "join", "on", "group", "by", "order", "limit", "count", "avg", "max", "min", "as", "and", "or", "in", "between", "desc", "asc"}
        for token in tokens:
            if token.lower() in keywords:
                continue
            if token not in candidates:
                candidates.append(token)
        return candidates

    def _concept(self, sql: str) -> str:
        lowered = sql.lower()
        for operation, concept in [('update', 'Updating records'), ('delete', 'Deleting records'), ('insert', 'Inserting records')]:
            if lowered.startswith(operation):
                return concept
        if re.search(r'\bgroup\s+by\b', lowered):
            return 'Grouped aggregation'
        for function, concept in [('sum', 'Total aggregation'), ('avg', 'Average aggregation'), ('max', 'Maximum value'), ('min', 'Minimum value'), ('count', 'Row counting')]:
            if re.search(rf'\b{function}\s*\(', lowered):
                return concept
        if re.search(r'\blike\b', lowered):
            return 'Pattern matching'
        if " join " in f" {lowered} ":
            return "Join and filter"
        if "group by" in lowered and "count(" in lowered:
            return "Aggregation with grouping"
        if "between" in lowered:
            return "Range filtering"
        if "order by" in lowered and "limit" in lowered:
            return "Ranking with limit"
        if "order by" in lowered:
            return "Sorting"
        if "in (" in lowered:
            return "Set-based filtering"
        if "where" in lowered:
            return "Conditional filtering"
        if lowered.startswith("select count("):
            return "Row counting"
        return "Data retrieval"

    def _expected_output(self, sql: str) -> str:
        lowered = sql.lower()
        if lowered.startswith(('update', 'delete', 'insert')):
            return 'A write status and affected-row count. With write simulation enabled, changes are previewed without modifying data.'
        if re.search(r'\bgroup\s+by\b', lowered):
            return 'One row per group, containing the selected grouping fields and aggregate values. HAVING, if present, filters these groups.'
        if re.search(r'\b(sum|avg|max|min|count)\s*\(', lowered) and not re.search(r'\bover\s*\(', lowered):
            return 'One summary row containing the selected aggregate values for the matching records.'
        if "count(" in lowered and "group by" in lowered:
            return "One row per group with the aggregated count value."
        if "count(" in lowered:
            return "A single row containing the count result."
        if re.search(r'\bjoin\b', lowered):
            return "Combined rows from the related tables that satisfy the join and filter conditions."
        if "order by" in lowered and "limit" in lowered:
            return "The top matching rows sorted in the requested order."
        if "order by" in lowered:
            return "Rows sorted according to the requested column."
        if "between" in lowered:
            return "Rows whose values fall inside the requested range."
        if "in (" in lowered:
            return "Rows matching one of the listed values."
        return "Rows that match the query conditions."

    def _optimization_tips(self, sql: str) -> List[str]:
        lowered = sql.lower()
        tips = []
        if "select *" in lowered:
            tips.append("Select only the columns you need to reduce I/O.")
        if "where" in lowered and "between" in lowered:
            tips.append("Range filters are efficient when the date column is indexed.")
        if "group by" in lowered:
            tips.append("Indexing the grouping column can improve aggregation performance.")
        if re.search(r'\bjoin\b', lowered):
            tips.append("Ensure join keys are indexed on both sides.")
        if "order by" in lowered:
            tips.append("An index on the sort column can help with ordering large result sets.")
        if "limit" in lowered:
            tips.append("LIMIT keeps the result set small and reduces transfer cost.")
        if not tips:
            tips.append("Keep filters explicit and avoid unnecessary columns for better performance.")
        return tips

    def explain(self, sql: str) -> Dict[str, object]:
        sql = sql.strip()
        lowered = sql.lower()
        tables = self._find_tables(sql)
        columns = self._find_columns(sql)
        concept = self._concept(sql)
        return {
            "sql_concept": concept,
            "query_explanation": self._build_explanation(sql),
            "expected_output": self._expected_output(sql),
            "optimization_tips": self._optimization_tips(sql),
            "summary": self._build_explanation(sql),
            "clauses_used": [clause.upper() for clause in ["join", "where", "group by", "order by", "limit", "having", "set"] if re.search(rf'\b{clause}\b', lowered)],
            "tables_involved": tables,
            "columns_involved": columns,
        }

    def _build_explanation(self, sql: str) -> str:
        sql = re.sub(r'\s+', ' ', sql.strip().rstrip(';'))
        lowered = sql.lower()
        parts = []
        tables = self._find_tables(sql)
        source = ', '.join(tables) or 'the query source'
        select = re.search(r'^select\s+(.*?)\s+from\b', sql, re.I)
        if select:
            fields = select.group(1)
            parts.append(f'Retrieves {"all columns" if fields == "*" else fields} from {source}.')
            labels = {'sum': 'total', 'avg': 'average', 'max': 'maximum', 'min': 'minimum', 'count': 'count'}
            for function, field in re.findall(r'\b(sum|avg|max|min|count)\s*\(([^)]*)\)', fields, re.I):
                target = 'matching rows' if field == '*' else f'{field} (non-null values)'
                parts.append(f'Calculates the {labels[function.lower()]} of {target}.')
        elif lowered.startswith('update'):
            parts.append(f'Updates records in {source}.')
        elif lowered.startswith('delete'):
            parts.append(f'Deletes matching records from {source}.')
        elif lowered.startswith('insert'):
            parts.append(f'Inserts new records into {source}.')
        for clause, description in [('where', 'Keeps records satisfying'), ('group by', 'Groups records by'), ('having', 'Keeps groups satisfying'), ('order by', 'Sorts the result by'), ('limit', 'Limits the returned rows to'), ('set', 'Assigns')]:
            match = re.search(rf'\b{clause}\s+(.+?)(?=\s+\b(?:group by|having|order by|limit|offset|returning|where)\b|$)', sql, re.I)
            if match:
                parts.append(f'{description} {match.group(1)}.')
        if re.search(r'\bjoin\b', lowered):
            parts.append("The query joins related tables to combine matching records.")
        if "between" in lowered:
            parts.append('BETWEEN includes both range endpoints.')
        if not parts:
            parts.append("The query retrieves data from the selected table.")
        return " ".join(parts)
