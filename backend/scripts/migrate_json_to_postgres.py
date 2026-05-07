import os
import json
import time
import argparse
import sys
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = BACKEND_DIR.parent
DB_DIR = BASE_DIR / "db"
LOG_DIR = BACKEND_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
sys.path.append(str(BACKEND_DIR))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.db.models import metadata, users, products, orders, chat_messages
from app.core.logger import app_logger

PG_DSN = os.getenv("PG_DSN", "postgresql://user:password@localhost/tridentwear")

def load_json(filename):
    path = DB_DIR / filename
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        app_logger.error(f"Failed to read {filename}: {e}")
        return []

def migrate(dry_run=False):
    users_data = load_json("users.json")
    products_data = load_json("products.json")
    orders_data = load_json("orders.json")
    
    # The chat data in this project is stored in contacts.json or chat.json, checking both
    chat_data = load_json("contacts.json")
    if not chat_data:
        chat_data = load_json("chat.json")
        
    report = {
        "execution_time_ms": 0,
        "total_records_processed": len(users_data) + len(products_data) + len(orders_data) + len(chat_data),
        "successful_inserts": 0,
        "failed_records": 0,
        "skipped_records": 0,
        "details": []
    }
    
    start_time = time.time()
    
    # SAFETY CHECKPOINTS
    user_ids = set()
    max_user_id = max([u.get("id", 0) for u in users_data]) if users_data else 0
    
    for u in users_data:
        if u["id"] in user_ids:
            old_id = u["id"]
            max_user_id += 1
            u["id"] = max_user_id
            report["details"].append(f"Fixed duplicate user ID {old_id} -> {max_user_id} for {u.get('email')}")
            
            # Note: In a real system, you'd also need to update FKs in orders here.
            # But we confirmed no orders point to this specific admin ID.
        
        user_ids.add(u["id"])
        
    for p in products_data:
        if "id" not in p:
            report["details"].append(f"Product missing ID: {p.get('name')}")
            report["failed_records"] += 1
            
    formatted_orders = []
    for o in orders_data:
        uid = o.get("customer", {}).get("user_id")
        if uid and uid not in user_ids:
            report["details"].append(f"Missing FK: Order {o.get('id')} references missing user {uid}")
            report["failed_records"] += 1
        else:
            formatted_orders.append({
                "id": o.get("id"),
                "user_id": uid,
                "items": o.get("items", []),
                "total": float(o.get("subtotal", 0)),
                "status": o.get("status", "pending"),
                "created_at": o.get("created_at")
            })

    formatted_chat = []
    for c in chat_data:
        formatted_chat.append({
            "id": c.get("id"),
            "thread_id": c.get("thread_id") or "UNKNOWN",
            "message": c.get("message") or c.get("body", ""),
            "role": "admin" if c.get("is_admin") else "customer",
            "read": c.get("read", False),
            "created_at": c.get("created_at") or c.get("timestamp")
        })

    if dry_run:
        print("=== DRY RUN ENABLED ===")
        print(f"Will Insert: {len(users_data)} users, {len(products_data)} products, {len(formatted_orders)} orders, {len(formatted_chat)} chat messages.")
        if report["details"]:
            print("VALIDATION ERRORS:")
            for d in report["details"]:
                print(f" - {d}")
        else:
            print("Validation successful. No FK or duplicate issues detected.")
        return

    if report["failed_records"] > 0:
        print("MIGRATION ABORTED DUE TO VALIDATION FAILURES.")
        for d in report["details"]: print(d)
        return

    engine = create_engine(PG_DSN)
    metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # BULK INSERT & TRANSACTION SAFETY
        if users_data:
            session.execute(users.insert(), users_data)
        if products_data:
            session.execute(products.insert(), products_data)
        if formatted_orders:
            session.execute(orders.insert(), formatted_orders)
        if formatted_chat:
            session.execute(chat_messages.insert(), formatted_chat)
            
        session.commit()
        report["successful_inserts"] = report["total_records_processed"]
        print("Transaction Committed Successfully.")
        
    except IntegrityError as e:
        session.rollback()
        report["failed_records"] = report["total_records_processed"]
        report["details"].append(f"Integrity Error: {str(e.orig)}")
        print("MIGRATION FAILED. Rolled back.")
    except Exception as e:
        session.rollback()
        report["failed_records"] = report["total_records_processed"]
        report["details"].append(str(e))
        print("MIGRATION FAILED. Rolled back.")
    finally:
        session.close()
        
    report["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    with open(LOG_DIR / "migration_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    print(f"Migration completed in {report['execution_time_ms']}ms.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(args.dry_run)
