import os
import json
import sys
from pathlib import Path
from sqlalchemy import create_engine, select, func

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent
DB_DIR = BASE_DIR / "db"
sys.path.append(str(BACKEND_DIR))

from app.db.models import metadata, users, products, orders, chat_messages
from app.core.logger import app_logger

PG_DSN = os.getenv("PG_DSN", "postgresql://user:password@localhost/tridentwear")

def load_json(filename):
    path = DB_DIR / filename
    if not path.exists():
        # Fallback to check if already archived
        archived_path = DB_DIR / f"{filename}.archive"
        if archived_path.exists():
            path = archived_path
        else:
            return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def verify():
    print("=== DATA PARITY VERIFICATION ===")
    
    users_data = load_json("users.json")
    products_data = load_json("products.json")
    orders_data = load_json("orders.json")
    chat_data = load_json("contacts.json")
    if not chat_data:
        chat_data = load_json("chat.json")
    
    engine = create_engine(PG_DSN)
    
    parity = True
    
    try:
        with engine.connect() as conn:
            pg_users_count = conn.execute(select(func.count()).select_from(users)).scalar()
            print(f"Users: JSON={len(users_data)} | PG={pg_users_count}")
            if len(users_data) != pg_users_count:
                print("❌ Mismatch in Users")
                parity = False
                
            pg_products_count = conn.execute(select(func.count()).select_from(products)).scalar()
            print(f"Products: JSON={len(products_data)} | PG={pg_products_count}")
            if len(products_data) != pg_products_count:
                print("❌ Mismatch in Products")
                parity = False
                
            pg_orders_count = conn.execute(select(func.count()).select_from(orders)).scalar()
            print(f"Orders: JSON={len(orders_data)} | PG={pg_orders_count}")
            if len(orders_data) != pg_orders_count:
                print("❌ Mismatch in Orders")
                parity = False
                
            pg_chat_count = conn.execute(select(func.count()).select_from(chat_messages)).scalar()
            print(f"Chat Messages: JSON={len(chat_data)} | PG={pg_chat_count}")
            if len(chat_data) != pg_chat_count:
                print("❌ Mismatch in Chat")
                parity = False
    except Exception as e:
        print(f"❌ Verification failed due to database connection error: {e}")
        parity = False

    if parity:
        print("\nAll records migrated successfully.")
        print("Archiving JSON files...")
        
        # Archiving logic - strictly renaming, never deleting
        for fname in ["users.json", "products.json", "orders.json", "contacts.json", "chat.json"]:
            fpath = DB_DIR / fname
            if fpath.exists():
                os.rename(fpath, DB_DIR / f"{fname}.archive")
                print(f" -> Archived {fname} to {fname}.archive")
                
        print("\nMIGRATION SAFE: TRUE")
    else:
        print("\nMIGRATION SAFE: FALSE")

if __name__ == "__main__":
    verify()
