import os
import re
import json
from dataclasses import dataclass
from typing import List, Dict, Any

import sqlparse
from anthropic import Anthropic

try:
    import google.genai as genai
    _GOOGLE_GENAI = "GENAI"
except ImportError:
    try:
        import google.generativeai as genai
        _GOOGLE_GENAI = "GENERATIVEAI"
    except ImportError:
        genai = None
        _GOOGLE_GENAI = None


@dataclass
class QueryCandidate:
    sql: str
    assumption: str


class QueryGenerationAgent:
    def __init__(self, schema_map, llm_client=None):
        self.schema_map = schema_map
        self.llm_client = llm_client
        self.llm_provider = os.getenv("LLM_PROVIDER", "ANTHROPIC").upper()
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        if not self.llm_client:
            self._init_client()

    def _tables(self):
        return set(self.schema_map.keys())

    def _columns_for(self, table):
        return {c["name"].lower(): c["name"] for c in self.schema_map.get(table, {}).get("columns", [])}

    def _validate_sql(self, sql: str) -> bool:
        if ";" in sql.strip().rstrip(";"):
            return False
        statements = sqlparse.parse(sql)
        if len(statements) != 1:
            return False
        lowered = sql.lower()
        banned = ["drop", "truncate", "alter", "grant", "revoke", "attach", "exec"]
        if any(re.search(rf"\b{kw}\b", lowered) for kw in banned):
            return False
        return True

    def _init_client(self):
        if self.llm_provider == "GOOGLE" and self.google_api_key and genai:
            if _GOOGLE_GENAI == "GENAI" and hasattr(genai, "Client"):
                self.client = genai.Client(api_key=self.google_api_key)
            elif _GOOGLE_GENAI == "GENERATIVEAI":
                genai.configure(api_key=self.google_api_key)
                self.client = genai
            else:
                self.client = None
            return
        if self.llm_provider == "ANTHROPIC" and self.anthropic_api_key:
            self.client = Anthropic(api_key=self.anthropic_api_key)
            return
        self.client = None

    def _find_table(self, nl: str) -> str | None:
        norm = nl.lower()
        tables = list(self.schema_map.keys())

        # Prefer explicit table keywords with business intent rules
        if 'employee' in norm or 'employees' in norm:
            if 'department' in norm and 'department' in self.schema_map:
                return 'Employee' if 'Employee' in self.schema_map else 'Department'
            return 'Employee' if 'Employee' in self.schema_map else None
        if 'student' in norm or 'students' in norm:
            return 'Students' if 'Students' in self.schema_map else None
        if 'department' in norm:
            return 'Department' if 'Department' in self.schema_map else None

        # prefer explicit table mention
        for table in tables:
            if table.lower() in norm or table.lower().rstrip('s') in norm or (table.lower() + 's') in norm:
                return table
        # fallback to column mentions
        for table, meta in self.schema_map.items():
            for column in meta.get('columns', []):
                if column['name'].lower() in norm:
                    return table
        return tables[0] if tables else None

    def _find_number(self, nl: str) -> int | None:
        currency_pattern = re.compile(
            r"(?:(?:₹|rs\.?|rupees?)\s*)?([\d][\d,\.]*\s*(?:k|m|lakh|lakhs|crore|crores)?)",
            re.IGNORECASE,
        )
        match = currency_pattern.search(nl)
        if not match:
            match = re.search(r"([\d][\d,\.]*\s*(?:k|m|lakh|lakhs|crore|crores)?)", nl, re.IGNORECASE)
        if match:
            number_text = match.group(1).strip().lower()
            multiplier = 1
            if number_text.endswith(("crores", "crore")):
                multiplier = 10_000_000
                number_text = number_text.rsplit(None, 1)[0]
            elif number_text.endswith(("lakhs", "lakh")):
                multiplier = 100_000
                number_text = number_text.rsplit(None, 1)[0]
            elif number_text.endswith("k"):
                multiplier = 1_000
                number_text = number_text[:-1]
            elif number_text.endswith("m"):
                multiplier = 1_000_000
                number_text = number_text[:-1]
            cleaned = re.sub(r"[^\d.]", "", number_text)
            if cleaned:
                try:
                    value = float(cleaned)
                    return int(value * multiplier)
                except ValueError:
                    return None
        return None

    def _preferred_column(self, table: str, candidates: List[str]) -> str:
        cols = self._columns_for(table)
        for col in candidates:
            if col in cols:
                return cols[col]
        return next(iter(cols.values()), 'id')

    def _build_where_clause(self, nl: str, table: str) -> str | None:
        norm = nl.lower()
        cols = self._columns_for(table)
        number = self._find_number(norm)

        if 'salary' in norm and number is not None:
            if 'at least' in norm or 'minimum' in norm:
                return f"salary >= {number}"
            if any(token in norm for token in ['greater than', 'above', 'over', 'exceed', 'exceeds', 'more than']):
                return f"salary > {number}"
            if 'at most' in norm:
                return f"salary <= {number}"
            if any(token in norm for token in ['less than', 'below', 'under']):
                return f"salary < {number}"
            if any(token in norm for token in ['equals', 'equal to', '=']):
                return f"salary = {number}"
        if 'gpa' in norm and number is not None:
            if 'at least' in norm or 'minimum' in norm:
                return f"gpa >= {number}"
            if any(token in norm for token in ['greater than', 'above', 'over', 'exceed', 'exceeds', 'more than']):
                return f"gpa > {number}"
            if 'at most' in norm:
                return f"gpa <= {number}"
            if any(token in norm for token in ['less than', 'below', 'under']):
                return f"gpa < {number}"
            if any(token in norm for token in ['equals', 'equal to', '=']):
                return f"gpa = {number}"
        if 'where' in norm:
            for col in cols:
                if col in norm and number is not None:
                    if 'greater than' in norm or 'above' in norm or 'over' in norm:
                        return f"{cols[col]} > {number}"
                    if 'less than' in norm or 'below' in norm or 'under' in norm:
                        return f"{cols[col]} < {number}"
                    if 'equals' in norm or 'equal to' in norm or '=' in norm:
                        return f"{cols[col]} = {number}"
        return None

    def _offline_candidates(self, nl: str, intent: str) -> List[QueryCandidate]:
        q = nl.lower()
        table = self._find_table(nl) or 'sqlite_schema'
        condition = self._build_where_clause(nl, table)
        candidates: List[QueryCandidate] = []

        if 'count' in q:
            candidates.append(QueryCandidate(f"SELECT COUNT(*) FROM {table};", f"Count rows from {table}"))
        if 'average' in q or 'avg' in q:
            col = self._preferred_column(table, ['salary', 'gpa', 'amount', 'score'])
            candidates.append(QueryCandidate(f"SELECT AVG({col}) AS average_value FROM {table};", f"Average {col} from {table}"))
        if 'max' in q or 'maximum' in q or 'highest' in q or 'largest' in q:
            col = self._preferred_column(table, ['salary', 'gpa', 'amount', 'score'])
            candidates.append(QueryCandidate(f"SELECT MAX({col}) AS max_value FROM {table};", f"Maximum {col} from {table}"))
        if 'min' in q or 'minimum' in q or 'lowest' in q or 'smallest' in q:
            col = self._preferred_column(table, ['salary', 'gpa', 'amount', 'score'])
            candidates.append(QueryCandidate(f"SELECT MIN({col}) AS min_value FROM {table};", f"Minimum {col} from {table}"))
        if 'top' in q and (m := re.search(r'top\s+(\d+)', q)):
            limit = int(m.group(1))
            col = self._preferred_column(table, ['salary', 'gpa', 'created_at', 'id'])
            candidates.append(QueryCandidate(f"SELECT * FROM {table} ORDER BY {col} DESC LIMIT {limit};", f"Top {limit} records from {table} by {col}"))

        if 'select' in q or 'show' in q or 'list' in q or 'find' in q or 'get' in q or 'all' in q:
            sql = f"SELECT * FROM {table}"
            if condition:
                sql += f" WHERE {condition}"
            sql += ";"
            candidates.append(QueryCandidate(sql, f"Select rows from {table}"))

        if not candidates:
            sql = f"SELECT * FROM {table}"
            if condition:
                sql += f" WHERE {condition}"
            sql += ";"
            candidates.append(QueryCandidate(sql, f"Fallback select from {table}"))

        return candidates

    def generate(self, nl: str, intent: str) -> List[Dict[str, Any]]:
        candidates = self._offline_candidates(nl, intent)
        if self.client:
            try:
                schema_blob = json.dumps(self.schema_map, indent=2)
                prompt = f"""
You are an NL-to-SQL assistant. Return JSON only with an array named candidates.
Use only tables and columns present in this schema:
{schema_blob}

User request: {nl}
Intent: {intent}

Each candidate must include sql and assumption.
Return 2-3 candidates if ambiguous. Keep SQL single-statement and valid.
"""
                if self.llm_provider == "ANTHROPIC":
                    response = self.client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=800,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    text = "".join(block.text for block in response.content if hasattr(block, "text"))
                else:
                    if _GOOGLE_GENAI == "GENAI" and hasattr(self.client, "chats"):
                        chat = self.client.chats.create(model="chat-bison-001")
                        response = chat.send_message(prompt)
                        text = getattr(response, "text", None) or str(response)
                    elif _GOOGLE_GENAI == "GENERATIVEAI" and hasattr(self.client, "chat") and hasattr(self.client.chat, "completions"):
                        response = self.client.chat.completions.create(
                            model="chat-bison-001",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2,
                        )
                        if getattr(response, "candidates", None):
                            candidate = response.candidates[0]
                            content = getattr(candidate, "content", None)
                            text = getattr(content, "text", None) if content is not None else str(candidate)
                        elif getattr(response, "last", None) is not None:
                            text = str(response.last)
                        else:
                            text = str(response)
                    elif hasattr(self.client, "responses") and hasattr(self.client.responses, "create"):
                        response = self.client.responses.create(
                            model="text-bison-001",
                            input=prompt,
                        )
                        if hasattr(response, "output") and response.output:
                            first_output = response.output[0]
                            if hasattr(first_output, "content") and first_output.content:
                                content = first_output.content
                                if isinstance(content, list) and content:
                                    text = getattr(content[0], "text", str(content[0]))
                                else:
                                    text = str(content)
                            else:
                                text = str(first_output)
                        else:
                            text = str(response)
                    else:
                        text = ""
                if text:
                    data = json.loads(text)
                    llm_candidates = [QueryCandidate(item["sql"], item.get("assumption", "LLM interpretation")) for item in data.get("candidates", [])]
                    if llm_candidates:
                        candidates = llm_candidates
            except Exception:
                pass
        results = []
        for c in candidates:
            if self._validate_sql(c.sql):
                results.append({"sql": c.sql, "assumption": c.assumption})
        return results
