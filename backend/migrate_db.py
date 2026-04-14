import json
import logging
import os
from pathlib import Path

from backend.database import engine, Base, SessionLocal
from backend.models import User, Product, Order

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
PRODUCTS_PATH = DB_DIR / "products.json"
USERS_PATH = DB_DIR / "users.json"
ORDERS_PATH = DB_DIR / "orders.json"

def migrate_data():
    # 1. Create tables
    logger.info("Dropping existing tables (if any) and creating new ones...")
    # NOTE: In production, use Alembic. Dropping tables is only for this initial migration of dev data.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # 2. Migrate Products
    if PRODUCTS_PATH.exists():
        logger.info("Migrating products...")
        with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            product_list = data.get("products", []) if isinstance(data, dict) else data
            
            for p_data in product_list:
                # Normalizing existing JSON data for the new schema
                price = p_data.get("price") or p_data.get("selling_price") or 0.0
                if isinstance(price, str):
                    price = float(price.replace("₹", "").replace(",", "").strip() or 0)
                
                orig_price = p_data.get("original_price")
                if isinstance(orig_price, str):
                    orig_price = float(orig_price.replace("₹", "").replace(",", "").strip() or price)

                sizes = p_data.get("sizes", [])
                if isinstance(sizes, dict):
                    # In some legacy formats sizes was a dict mapping size to stock
                    sizes = list(sizes.keys())
                elif not sizes:
                    # Generic sizes if missing
                    sizes = ["S", "M", "L", "XL"]

                product = Product(
                    id=p_data.get("id"),
                    name=p_data.get("name", "Unnamed Product"),
                    description=p_data.get("description", p_data.get("copy", "")),
                    price=price,
                    original_price=orig_price,
                    category=p_data.get("category", p_data.get("type", "t-shirt")),
                    tags=p_data.get("tags", []),
                    sizes=sizes,
                    image=p_data.get("image", p_data.get("images", [None])[0]),
                    images=p_data.get("images", []),
                    in_stock=p_data.get("in_stock", True)
                )
                # Keep ID if it exists in JSON to preserve relationships if any
                db.add(product)
        db.commit()

    # 3. Migrate Users
    if USERS_PATH.exists():
        logger.info("Migrating users...")
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            users_data = json.load(f)
            
            user_list = users_data if isinstance(users_data, list) else [
                {"email": k, **v} if isinstance(v, dict) else v 
                for k, v in users_data.items()
            ]

            for u_data in user_list:
                email = getattr(u_data, "get", lambda x: "")("email") or getattr(u_data, "get", lambda x: "")("id", "user@tridentwear.com")
                user = User(
                    name=u_data.get("name", "User"),
                    email=email.lower(),
                    password_hash=u_data.get("password", ""), # In json this was hashed
                    is_admin=u_data.get("is_admin", False)
                )
                db.add(user)
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error migrating users: {e}")
            db.rollback()

    # NOTE: Skipping orders/cart migration as these are usually ephemeral in dev. We start fresh with Orders/Cart table.

    logger.info("Migration complete!")
    db.close()

if __name__ == "__main__":
    migrate_data()
