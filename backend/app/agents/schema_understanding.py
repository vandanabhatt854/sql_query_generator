from sqlalchemy import inspect


class SchemaUnderstandingAgent:
    def __init__(self, engine):
        self.engine = engine
        self.schema_map = {}

    def refresh(self):
        inspector = inspect(self.engine)
        schema = {}
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            fks = inspector.get_foreign_keys(table_name)
            relationships = []
            for fk in fks:
                relationships.append({
                    "columns": fk.get("constrained_columns", []),
                    "referred_table": fk.get("referred_table"),
                    "referred_columns": fk.get("referred_columns", []),
                })
            schema[table_name] = {
                "columns": [
                    {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
                    for c in columns
                ],
                "relationships": relationships,
            }
        self.schema_map = schema
        return schema

