from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import random
import re
import shutil
import smtplib
import ssl
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.exceptions import StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent

# ── Frontend layout ──────────────────────────────────────────────────────────
FRONTEND_ROOT  = BASE_DIR / "frontend"          # d:\TridentWear\frontend
ASSETS_DIR     = FRONTEND_ROOT / "assets"       # frontend/assets/
COMPONENTS_DIR = FRONTEND_ROOT / "components"   # frontend/components/
IMAGES_DIR     = ASSETS_DIR / "images"          # frontend/assets/images/
UPLOADS_DIR    = IMAGES_DIR / "uploads"         # frontend/assets/images/uploads/

# Page → file mapping (flat filename → actual subpath)
PAGE_FILE_MAP: dict[str, Path] = {
    "index.html":         FRONTEND_ROOT / "index.html",
    "products.html":      FRONTEND_ROOT / "pages" / "shop"    / "products.html",
    "cart.html":          FRONTEND_ROOT / "pages" / "shop"    / "cart.html",
    "product.html":       FRONTEND_ROOT / "pages" / "shop"    / "product.html",
    "checkout.html":      FRONTEND_ROOT / "pages" / "shop"    / "checkout.html",
    "wishlist.html":      FRONTEND_ROOT / "pages" / "shop"    / "wishlist.html",
    "login.html":         FRONTEND_ROOT / "pages" / "account" / "login.html",
    "register.html":      FRONTEND_ROOT / "pages" / "account" / "register.html",
    "profile.html":       FRONTEND_ROOT / "pages" / "account" / "profile.html",
    "profile-setup.html": FRONTEND_ROOT / "pages" / "account" / "profile-setup.html",
    "verify.html":        FRONTEND_ROOT / "pages" / "account" / "verify.html",
    "about.html":         FRONTEND_ROOT / "pages" / "info"    / "about.html",
    "contact.html":       FRONTEND_ROOT / "pages" / "info"    / "contact.html",
    "admin.html":         FRONTEND_ROOT / "pages" / "admin"   / "admin.html",
    "privacy.html":       FRONTEND_ROOT / "pages" / "legal"   / "privacy.html",
    "terms.html":         FRONTEND_ROOT / "pages" / "legal"   / "terms.html",
    "returns.html":       FRONTEND_ROOT / "pages" / "legal"   / "returns.html",
    "shipping.html":      FRONTEND_ROOT / "pages" / "legal"   / "shipping.html",
    "track.html":         FRONTEND_ROOT / "pages" / "support" / "track.html",
    "404.html":           FRONTEND_ROOT / "pages" / "error"   / "404.html",
}

# ── Database layout ───────────────────────────────────────────────────────────
DB_DIR = BASE_DIR / "db"
PRODUCTS_PATH  = DB_DIR / "products.json"
ORDERS_PATH    = DB_DIR / "orders.json"
USERS_PATH     = DB_DIR / "users.json"
CONTACTS_PATH  = DB_DIR / "contacts.json"
REVIEWS_PATH   = DB_DIR / "reviews.json"
COUPONS_PATH   = DB_DIR / "coupons.json"
WISHLIST_PATH  = DB_DIR / "wishlist.json"
CHAT_PATH      = DB_DIR / "chat.json"

# Mirror products.json into frontend/assets/data/ for JS static-mode fallback
FRONTEND_PRODUCTS_PATH = FRONTEND_ROOT / "assets" / "data" / "products.json"

PASSWORD_ITERATIONS = 120_000
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
JWT_SECRET = os.getenv("TRIDENT_JWT_SECRET", os.getenv("JWT_SECRET", "trident-super-secret-key-12345"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("TRIDENT_JWT_EXPIRATION_DAYS", "7"))
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REVOKED_TOKEN_IDS: set[str] = set()





class OTPPayload(BaseModel):
    phone: str
    otp: Optional[str] = None
    name: Optional[str] = None


class GooglePayload(BaseModel):
    credential: str




class ForgotPasswordPayload(BaseModel):
    email: str

class ResetPasswordPayload(BaseModel):
    email: str
    otp: str
    new_password: str

class ReviewPayload(BaseModel):
    product_id: int
    rating: int
    review: str

class OrderStatusUpdate(BaseModel):
    status: str


class CouponPayload(BaseModel):
    code: str
    discount: float          # percent (1-100)
    expiry: str              # ISO date string YYYY-MM-DD
    usage_limit: int = 100

class ApplyCouponPayload(BaseModel):
    code: str
    subtotal: float

class WishlistPayload(BaseModel):
    product_id: int

class CODPayload(BaseModel):
    items: List[Dict[str, Any]]
    subtotal: float
    customer: Dict[str, Any]
    shipping: Dict[str, Any]
    coupon_code: Optional[str] = None

class RazorpayCreatePayload(BaseModel):
    amount: int              # paise
    currency: str = "INR"

class RazorpayVerifyPayload(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    order_data: Dict[str, Any]


class ChatMessagePayload(BaseModel):
    message: str
    admin_reply: bool = False
    thread_id: Optional[str] = None

class ContactPayload(BaseModel):
    name: str
    email: str
    message: str


class OrderPayload(BaseModel):
    items: List[Dict[str, Any]]
    subtotal: float
    customer: Dict[str, Any]
    shipping: Dict[str, Any]


DEFAULT_PRODUCTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "Classic Black Tee",
        "category": "tshirt",
        "price": 799,
        "description": "Premium 220 GSM cotton crew neck tee in timeless black. Relaxed fit, pre-shrunk fabric.",
        "image": "/images/black-tshirt.png",
        "tag": "Bestseller",
        "sizes": ["S", "M", "L", "XL", "XXL"],
        "stock": 150,
        "featured": True,
    },
    {
        "id": 2,
        "name": "White Minimal Tee",
        "category": "tshirt",
        "price": 699,
        "description": "Clean white tee with a minimal cut. 200 GSM bio-washed cotton for an ultra-soft feel.",
        "image": "/images/white-tshirt.png",
        "tag": "New Drop",
        "sizes": ["S", "M", "L", "XL"],
        "stock": 200,
        "featured": True,
    },
    {
        "id": 3,
        "name": "Navy Formal Shirt",
        "category": "shirt",
        "price": 1299,
        "description": "Slim-fit navy blue formal shirt with wrinkle-resistant fabric built for all-day structure.",
        "image": "/images/navy-shirt.png",
        "tag": "Premium",
        "sizes": ["S", "M", "L", "XL"],
        "stock": 80,
        "featured": True,
    },
    {
        "id": 4,
        "name": "Olive Casual Shirt",
        "category": "shirt",
        "price": 1099,
        "description": "Relaxed-fit olive button-up with breathable cotton blend and easy street-luxury styling.",
        "image": "/images/olive-shirt.png",
        "tag": "Street Essential",
        "sizes": ["M", "L", "XL", "XXL"],
        "stock": 120,
        "featured": True,
    },
    {
        "id": 5,
        "name": "Charcoal Oversized Tee",
        "category": "tshirt",
        "price": 899,
        "description": "Oversized drop-shoulder tee in charcoal grey. Heavy cotton weight with a clean structured drape.",
        "image": "/images/grey-tshirt.png",
        "tag": "Trending",
        "sizes": ["M", "L", "XL", "XXL"],
        "stock": 100,
        "featured": False,
    },
    {
        "id": 6,
        "name": "Stone Linen Shirt",
        "category": "shirt",
        "price": 1199,
        "description": "Lightweight linen-blend shirt in a clean stone tone with a refined mandarin collar finish.",
        "image": "/images/olive-shirt.png",
        "tag": "Summer Edit",
        "sizes": ["S", "M", "L", "XL"],
        "stock": 90,
        "featured": False,
    },
]

DEFAULT_ADMIN = {
    "id": 1,
    "name": "Trident Admin",
    "email": "admin@trident.local",
    "password_hash": "$2b$12$7Q07pQBBqNur7Rdxq4R7pebAeUdR89zN4T.NQfpcPZ/p4CVB3TRJq",
    "role": "admin",
    "created_at": "2026-04-12T00:00:00+00:00",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def normalize_image_path(value: str) -> str:
    image_value = str(value or "").strip()
    if not image_value:
        return "/images/hero-banner.png"
    if image_value.startswith("/images/"):
        return image_value
    if image_value.startswith("../images/"):
        return f"/images/{Path(image_value).name}"
    return f"/images/{Path(image_value).name}"


def normalize_sizes(value: Any) -> List[str]:
    if isinstance(value, list):
        sizes = [str(size).strip().upper() for size in value if str(size).strip()]
    else:
        sizes = [segment.strip().upper() for segment in str(value or "").split(",") if segment.strip()]
    return sizes or ["S", "M", "L", "XL"]


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def normalize_product(raw_product: Dict[str, Any], index: int = 0) -> Dict[str, Any]:
    return {
        "id": int(raw_product.get("id", index + 1)),
        "name": str(raw_product.get("name", "")).strip(),
        "category": "shirt" if str(raw_product.get("category", "")).strip().lower() == "shirt" else "tshirt",
        "price": int(float(raw_product.get("price", 0) or 0)),
        "description": str(raw_product.get("description", "")).strip(),
        "image": normalize_image_path(str(raw_product.get("image", ""))),
        "tag": str(raw_product.get("tag", "")).strip(),
        "sizes": normalize_sizes(raw_product.get("sizes", [])),
        "stock": max(int(float(raw_product.get("stock", 0) or 0)), 0),
        "featured": normalize_bool(raw_product.get("featured", index < 4)),
    }


def product_sort_key(product: Dict[str, Any]) -> Any:
    return (product["category"] != "tshirt", not product["featured"], product["id"])


def load_products() -> List[Dict[str, Any]]:
    raw_products = read_json(PRODUCTS_PATH, DEFAULT_PRODUCTS)
    products = [normalize_product(product, index) for index, product in enumerate(raw_products)]
    return sorted(products, key=product_sort_key)


def save_products(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = [normalize_product(product, index) for index, product in enumerate(products)]
    normalized.sort(key=product_sort_key)
    write_json(PRODUCTS_PATH, normalized)
    write_json(FRONTEND_PRODUCTS_PATH, normalized)
    return normalized


def load_orders() -> List[Dict[str, Any]]:
    return read_json(ORDERS_PATH, [])


def save_orders(orders: List[Dict[str, Any]]) -> None:
    write_json(ORDERS_PATH, orders)



def load_reviews() -> List[Dict[str, Any]]:
    return read_json(REVIEWS_PATH, [])

def save_reviews(reviews: List[Dict[str, Any]]) -> None:
    write_json(REVIEWS_PATH, reviews)

def load_users() -> List[Dict[str, Any]]:
    return read_json(USERS_PATH, [DEFAULT_ADMIN])


def save_users(users: List[Dict[str, Any]]) -> None:
    write_json(USERS_PATH, users)



def load_chat() -> List[Dict[str, Any]]:
    return read_json(CHAT_PATH, [])

def save_chat(chats: List[Dict[str, Any]]) -> None:
    write_json(CHAT_PATH, chats)

# Note: create_shiprocket_shipment is defined below near the Shiprocket section

def load_contacts() -> List[Dict[str, Any]]:
    return read_json(CONTACTS_PATH, [])


def save_contacts(contacts: List[Dict[str, Any]]) -> None:
    write_json(CONTACTS_PATH, contacts)



def load_coupons() -> List[Dict[str, Any]]:
    return read_json(COUPONS_PATH, [])

def save_coupons(coupons: List[Dict[str, Any]]) -> None:
    write_json(COUPONS_PATH, coupons)

def load_wishlist() -> List[Dict[str, Any]]:
    return read_json(WISHLIST_PATH, [])

def save_wishlist(items: List[Dict[str, Any]]) -> None:
    write_json(WISHLIST_PATH, items)

def deduct_stock(order_items: List[Dict[str, Any]]) -> None:
    """Reduce product stock after an order is saved."""
    products = load_products()
    product_map = {p["id"]: p for p in products}
    for item in order_items:
        pid = int(item.get("id", 0))
        qty = int(item.get("qty", 1))
        if pid in product_map:
            product_map[pid]["stock"] = max(0, product_map[pid]["stock"] - qty)
    save_products(list(product_map.values()))

def validate_coupon(code: str, subtotal: float) -> Dict[str, Any]:
    """Returns coupon dict or raises HTTPException."""
    coupons = load_coupons()
    now = datetime.now(timezone.utc).date()
    for c in coupons:
        if c.get("code", "").upper() == code.strip().upper():
            # Check expiry
            try:
                expiry_date = datetime.fromisoformat(c["expiry"]).date()
            except Exception:
                expiry_date = now
            if expiry_date < now:
                raise HTTPException(status_code=400, detail="Coupon has expired.")
            if c.get("usage_count", 0) >= c.get("usage_limit", 1):
                raise HTTPException(status_code=400, detail="Coupon usage limit reached.")
            discount_amount = round(subtotal * c["discount"] / 100, 2)
            return {
                **c,
                "discount_pct": c["discount"],
                "discount_amount": discount_amount,
                "final_total": round(subtotal - discount_amount, 2),
            }
    raise HTTPException(status_code=404, detail="Invalid coupon code.")

def use_coupon(code: str) -> None:
    coupons = load_coupons()
    for c in coupons:
        if c.get("code", "").upper() == code.strip().upper():
            c["usage_count"] = c.get("usage_count", 0) + 1
    save_coupons(coupons)

def send_order_email(order: Dict[str, Any]) -> None:
    """Non-blocking email; silently skips if SMTP not configured."""
    from email.mime.text import MIMEText
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASS", "")
    if not (host and user and password):
        return
    to_email = order.get("customer", {}).get("email", "")
    if not to_email:
        return
    items_text = ", ".join(
        f"{i['name']} x{i['qty']}" for i in order.get("items", [])
    )
    body = (
        f"Hi {order['customer'].get('name', 'Customer')},\n\n"
        f"Your TridentWear order {order['order_id']} has been placed!\n"
        f"Status: {order.get('status','confirmed')}\n"
        f"Items: {items_text}\n"
        f"Total: \u20b9{order.get('subtotal', 0)}\n\n"
        f"Thank you for shopping with us!\n\nTeam TridentWear"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"Order Confirmed – {order['order_id']}"
    msg["From"] = user
    msg["To"] = to_email
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(host, port) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ctx)
            smtp.login(user, password)
            smtp.sendmail(user, [to_email], msg.as_string())
    except Exception:
        pass  # Never crash the order flow

def next_id(items: List[Dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(item.get("id", 0)) for item in items) + 1


def serialize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
        "gender": user.get("gender"),
        "phone": user.get("phone"),
        "user_id": user.get("user_id"),
        "profile_completed_status": user.get("profile_completed_status", True),
    }


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    _ = salt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_legacy_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_encoded, digest_encoded = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_text)
        salt_bytes = base64.b64decode(salt_encoded.encode("utf-8"))
        expected = base64.b64decode(digest_encoded.encode("utf-8"))
    except (TypeError, ValueError):
        return False

    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations)
    return hmac.compare_digest(computed, expected)


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("pbkdf2_sha256$"):
        return verify_legacy_password(password, stored_hash)
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        return False


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    target = email.strip().lower()
    for user in load_users():
        if user.get("email", "").lower() == target:
            return user
    return None


def find_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    for user in load_users():
        if int(user.get("id", 0)) == int(user_id):
            return user
    return None


def update_user(user_id: int, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    users = load_users()
    updated_user: Optional[Dict[str, Any]] = None

    for index, user in enumerate(users):
        if int(user.get("id", 0)) != int(user_id):
            continue
        users[index] = {**user, **changes}
        updated_user = users[index]
        break

    if updated_user is None:
        return None

    save_users(users)
    return updated_user


def issue_auth_token(user: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRATION_DAYS),
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def revoke_auth_token(token: Optional[str]) -> None:
    if not token:
        return
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
    except jwt.PyJWTError:
        return

    token_id = payload.get("jti")
    if token_id:
        REVOKED_TOKEN_IDS.add(str(token_id))


def get_request_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    token = request.headers.get("x-session-token", "").strip()
    return token or None


def store_session_user(request: Request, user: Dict[str, Any]) -> None:
    request.session.clear()
    request.session["user_id"] = int(user["id"])


def upgrade_password_hash_if_needed(user: Dict[str, Any], password: str) -> Dict[str, Any]:
    stored_hash = user.get("password_hash", "")
    if not stored_hash.startswith("pbkdf2_sha256$"):
        return user

    upgraded_user = update_user(user["id"], {"password_hash": hash_password(password)})
    return upgraded_user or user


def get_session_user(request: Request) -> Optional[Dict[str, Any]]:
    token = get_request_token(request)
    user_id = None
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("jti") in REVOKED_TOKEN_IDS:
                raise jwt.InvalidTokenError("Token has been revoked.")
            user_id = payload.get("sub")
        except jwt.PyJWTError:
            pass

    if not user_id:
        user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = find_user_by_id(int(user_id))
    if user:
        return user

    request.session.clear()
    return None


def require_admin(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in first.")
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_PATTERN.match(normalized):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address.")
    return normalized





DEFAULT_COUPONS: List[Dict[str, Any]] = [
    {
        "code": "TRIDENTFIRST",
        "discount": 20,
        "expiry": "2027-12-31",
        "usage_limit": 1000,
        "usage_count": 0,
    },
    {
        "code": "TRIDENT10",
        "discount": 10,
        "expiry": "2027-12-31",
        "usage_limit": 5000,
        "usage_count": 0,
    },
]


def ensure_data_files() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    products = load_products()
    save_products(products)

    orders = read_json(ORDERS_PATH, [])
    write_json(ORDERS_PATH, orders)

    users = read_json(USERS_PATH, [])
    if not users:
        users = [DEFAULT_ADMIN]
    if not any(user.get("email", "").lower() == DEFAULT_ADMIN["email"] for user in users):
        users.insert(0, DEFAULT_ADMIN)
    save_users(users)

    contacts = read_json(CONTACTS_PATH, [])
    write_json(CONTACTS_PATH, contacts)

    # Seed reviews and coupons if files are missing or empty
    if not REVIEWS_PATH.exists():
        write_json(REVIEWS_PATH, [])

    if not COUPONS_PATH.exists() or not read_json(COUPONS_PATH, []):
        write_json(COUPONS_PATH, DEFAULT_COUPONS)

    if not WISHLIST_PATH.exists():
        write_json(WISHLIST_PATH, [])

    if not CHAT_PATH.exists():
        write_json(CHAT_PATH, [])


app = FastAPI(title="Trident Premium Store", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("TRIDENT_SESSION_SECRET", "trident-local-session-secret"),
    same_site="lax",
    https_only=os.getenv("ENVIRONMENT", "development") == "production",
)

ensure_data_files()


auth_router = APIRouter(tags=["auth"])
products_router = APIRouter(prefix="/api", tags=["products"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
orders_router = APIRouter(prefix="/api", tags=["orders"])
contact_router = APIRouter(prefix="/api", tags=["contact"])
payment_router = APIRouter(prefix="/api/payment", tags=["payment"])
coupon_router = APIRouter(prefix="/api", tags=["coupons"])
wishlist_router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])

@wishlist_router.get("")
@wishlist_router.get("/")
def get_user_wishlist(request: Request) -> List[Dict[str, Any]]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to view your wishlist.")
    wishlists = load_wishlist()
    user_items = [w for w in wishlists if w.get("user_id") == user["id"]]
    products = {p["id"]: p for p in load_products()}
    enriched = []
    for w in user_items:
        if w["product_id"] in products:
            enriched.append({
                "id": w["id"],
                "product_id": w["product_id"],
                "product": products[w["product_id"]]
            })
    return enriched

@wishlist_router.post("/add")
def add_to_wishlist(payload: WishlistPayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to manage your wishlist.")
    wishlists = load_wishlist()
    if any(w.get("user_id") == user["id"] and w.get("product_id") == payload.product_id for w in wishlists):
        return {"success": True, "message": "Already in wishlist"}
    products = load_products()
    if not any(p["id"] == payload.product_id for p in products):
        raise HTTPException(status_code=404, detail="Product not found.")
    new_item = {
        "id": next_id(wishlists),
        "user_id": user["id"],
        "product_id": payload.product_id,
        "created_at": now_iso()
    }
    wishlists.append(new_item)
    save_wishlist(wishlists)
    return {"success": True, "message": "Added to wishlist", "item": new_item}

@wishlist_router.delete("/remove")
def remove_from_wishlist(payload: WishlistPayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to manage your wishlist.")
    wishlists = load_wishlist()
    initial_len = len(wishlists)
    wishlists = [w for w in wishlists if not (w.get("user_id") == user["id"] and w.get("product_id") == payload.product_id)]
    if len(wishlists) == initial_len:
         raise HTTPException(status_code=404, detail="Item not in wishlist.")
    save_wishlist(wishlists)
    return {"success": True, "message": "Removed from wishlist"}

@coupon_router.post("/coupons/apply")
def apply_coupon(payload: ApplyCouponPayload) -> Dict[str, Any]:
    return validate_coupon(payload.code, payload.subtotal)















@auth_router.post("/api/auth/otp/send")
def send_otp(payload: OTPPayload) -> Dict[str, Any]:
    # Development dummy OTP
    return {"success": True, "message": "OTP sent! (Dev Mode OTP: 123456)", "dev_otp": "123456"}


@auth_router.post("/api/auth/otp/verify")
def verify_otp(payload: OTPPayload, request: Request) -> Dict[str, Any]:
    if payload.otp != "123456":
         raise HTTPException(status_code=400, detail="Invalid OTP.")
    users = load_users()
    email_variant = f"{payload.phone}@trident.local"
    user = find_user_by_email(email_variant)
    if not user:
        user = {
            "id": next_id(users),
            "name": payload.name,
            "email": email_variant,
            "phone": payload.phone,
            "password_hash": hash_password("dummy"),
            "role": "customer",
            "created_at": now_iso(),
        }
        users.append(user)
        save_users(users)
    
    store_session_user(request, user)
    token = issue_auth_token(user)
    return {"success": True, "message": "OTP verified.", "token": token, "user": serialize_user(user)}

@auth_router.post("/api/auth/password/forgot")
def forgot_password(payload: ForgotPasswordPayload) -> Dict[str, Any]:
    email = validate_email(payload.email)
    users = load_users()
    user_idx = next((i for i, u in enumerate(users) if u.get("email", "").lower() == email), None)
    if user_idx is None:
        # Always return success to prevent email enumeration
        return {"success": True, "message": "If an account exists, a reset OTP was sent."}
    
    otp = str(random.randint(100000, 999999))
    users[user_idx]["otp"] = otp
    users[user_idx]["otp_expiry"] = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    save_users(users)
    
    # Normally send email here. In dev we return it:
    return {"success": True, "message": f"If an account exists, a reset OTP was sent. (Dev Mode OTP: {otp})", "dev_otp": otp}

@auth_router.post("/api/auth/password/reset")
def reset_password(payload: ResetPasswordPayload) -> Dict[str, Any]:
    email = validate_email(payload.email)
    users = load_users()
    user_idx = next((i for i, u in enumerate(users) if u.get("email", "").lower() == email), None)
    
    if user_idx is None:
        raise HTTPException(status_code=400, detail="Invalid email or OTP.")
        
    user = users[user_idx]
    if user.get("otp") != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
        
    expiry = user.get("otp_expiry")
    if expiry and datetime.fromisoformat(expiry) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP has expired.")
        
    if len(payload.new_password) < 8:
         raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    users[user_idx]["password_hash"] = hash_password(payload.new_password)
    users[user_idx]["otp"] = None
    save_users(users)
    
    return {"success": True, "message": "Password reset successfully. You can now log in."}



class EmailVerifyPayload(BaseModel):
    email: str
    otp: str

@auth_router.post("/verify-otp")
@auth_router.post("/api/auth/otp/verify-email")
def verify_email_registration(payload: EmailVerifyPayload, request: Request) -> Dict[str, Any]:
    users = load_users()
    target_email = validate_email(payload.email)
    user_idx = next((i for i, u in enumerate(users) if u.get("email") == target_email), None)
    
    if user_idx is None:
        raise HTTPException(status_code=404, detail="User not found.")
        
    user = users[user_idx]
    if user.get("otp_verification_status"):
        raise HTTPException(status_code=400, detail="Account already verified.")
        
    if user.get("otp") != payload.otp.strip():
        raise HTTPException(status_code=400, detail="Incorrect OTP.")
        
    # Check expiry
    expiry = user.get("otp_expiry")
    if expiry and datetime.fromisoformat(expiry) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")

    user["otp_verification_status"] = True
    users[user_idx] = user
    save_users(users)
    
    # Authenticate user immediately after verification
    store_session_user(request, user)
    token = issue_auth_token(user)
    
    return {"success": True, "message": "Email verified successfully.", "token": token, "user": serialize_user(user)}

class ProfileSetupPayload(BaseModel):
    gender: str
    phone: Optional[str] = None

@auth_router.post("/api/auth/profile/setup")
def setup_profile(payload: ProfileSetupPayload, request: Request) -> Dict[str, Any]:
    user_auth = get_session_user(request)
    if not user_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    users = load_users()
    user_idx = next((i for i, u in enumerate(users) if u.get("id") == user_auth["id"]), None)
    if user_idx is not None:
        u = users[user_idx]
        u["gender"] = payload.gender
        if payload.phone:
            u["phone"] = payload.phone
        u["profile_completed_status"] = True
        users[user_idx] = u
        save_users(users)
        return {"success": True, "message": "Profile setup complete", "user": serialize_user(u)}
    raise HTTPException(status_code=404, detail="User not found.")

















# ─── All include_router() calls are at the END of this file ───
# (Routes must be fully defined before include_router copies them)


@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and "text/html" in request.headers.get("accept", ""):
        try:
            return html_response("404.html")
        except Exception:
            pass
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

@products_router.post("/reviews")
def create_review(payload: ReviewPayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You must be logged in to review products.")
    
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5.")
        
    reviews = load_reviews()
    # Check if user already reviewed
    for r in reviews:
        if r["user_id"] == user["id"] and r["product_id"] == payload.product_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this product.")
            
    review = {
        "id": next_id(reviews),
        "user_id": user["id"],
        "user_name": user["name"],
        "product_id": payload.product_id,
        "rating": payload.rating,
        "review": payload.review.strip(),
        "created_at": now_iso()
    }
    reviews.append(review)
    save_reviews(reviews)
    return {"success": True, "message": "Review submitted successfully.", "review": review}

@products_router.get("/reviews/{product_id}")
def get_reviews(product_id: int) -> List[Dict[str, Any]]:
    reviews = load_reviews()
    return [r for r in reviews if r["product_id"] == product_id]

# ════════════════════════════════════════════════════════════
# SHIPROCKET HELPERS
# ════════════════════════════════════════════════════════════





# ════════════════════════════════════════════════════════════
# ADVANCED AUTH (OTP & GOOGLE)
# ════════════════════════════════════════════════════════════


@auth_router.post("/api/auth/google")
def google_auth(payload: GooglePayload, request: Request) -> Dict[str, Any]:
    try:
        decoded_token = jwt.decode(payload.credential, options={"verify_signature": False})
        email = decoded_token.get("email")
        name = decoded_token.get("name", "Google User")
        
        if not email:
            raise HTTPException(status_code=400, detail="Invalid Google credential: No email found.")
            
        email = validate_email(email)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process Google sign-in: {str(e)}")

    users = load_users()
    user = find_user_by_email(email)
    if not user:
        user = {
            "id": next_id(users),
            "name": name,
            "email": email,
            "role": "customer",
            "profile_completed_status": True,
            "otp_verification_status": True,
            "created_at": now_iso()
        }
        users.append(user)
        save_users(users)
        
    store_session_user(request, user)
    token = issue_auth_token(user)
    return {"success": True, "token": token, "user": serialize_user(user)}



# ════════════════════════════════════════════════════════════
# CHECKOUT & PAYMENT SYSTEM
# ════════════════════════════════════════════════════════════
# payment_router is declared at the top with other routers — see line 721






# ════════════════════════════════════════════════════════════
# ROUTER REGISTRATION — must come AFTER all route decorators
# ════════════════════════════════════════════════════════════
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(admin_router)
app.include_router(orders_router)
app.include_router(contact_router)
app.include_router(wishlist_router)
app.include_router(coupon_router)
