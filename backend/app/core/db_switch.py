import os
from app.db.database import DatabaseInterface, JsonDatabaseAdapter, PostgresDatabaseAdapter, DualWriteDatabaseAdapter

DB_MODE = os.getenv("DB_MODE", "json") # "json", "postgres", "dual_write"
PG_DSN = os.getenv("PG_DSN", "postgresql://user:password@localhost/tridentwear")

def get_db() -> DatabaseInterface:
    json_adapter = JsonDatabaseAdapter()
    
    if DB_MODE == "json":
        return json_adapter
    elif DB_MODE == "postgres":
        return PostgresDatabaseAdapter(PG_DSN)
    elif DB_MODE == "dual_write":
        pg_adapter = PostgresDatabaseAdapter(PG_DSN)
        return DualWriteDatabaseAdapter(old_db=json_adapter, new_db=pg_adapter)
    else:
        return json_adapter

db = get_db()
