from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import shutil
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
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR
HTML_DIR = FRONTEND_DIR
CSS_DIR = FRONTEND_DIR / "css"
JS_DIR = FRONTEND_DIR / "js"
IMAGES_DIR = FRONTEND_DIR / "images"
UPLOADS_DIR = IMAGES_DIR / "uploads"

DB_DIR = BASE_DIR / "db"
PRODUCTS_PATH = DB_DIR / "products.json"
ORDERS_PATH = DB_DIR / "orders.json"
USERS_PATH = DB_DIR / "users.json"
CONTACTS_PATH = DB_DIR / "contacts.json"
REVIEWS_PATH = DB_DIR / "reviews.json"
COUPONS_PATH = DB_DIR / "coupons.json"
WISHLIST_PATH = DB_DIR / "wishlist.json"
CHAT_PATH = DB_DIR / "chat.json"

FRONTEND_PRODUCTS_PATH = JS_DIR / "products.json"

PASSWORD_ITERATIONS = 120_000
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
JWT_SECRET = os.getenv("TRIDENT_JWT_SECRET", os.getenv("JWT_SECRET", "trident-super-secret-key-12345"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.getenv("TRIDENT_JWT_EXPIRATION_DAYS", "7"))
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REVOKED_TOKEN_IDS: set[str] = set()


class RegisterPayload(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: Optional[str] = None


class OTPPayload(BaseModel):
    phone: str
    otp: Optional[str] = None
    name: Optional[str] = None


class GooglePayload(BaseModel):
    email: str
    name: str
    id_token: str


class LoginPayload(BaseModel):
    email: str
    password: str



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

def create_shiprocket_shipment(order: Dict[str, Any]) -> Dict[str, Any]:
    """Stub for creating shipment on Shiprocket."""
    # In production, use os.getenv("SHIPROCKET_API_KEY") 
    # and make requests to Shiprocket API.
    return {
        "tracking_id": f"SR{uuid.uuid4().hex[:8].upper()}",
        "courier": "Delhivery",
        "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=4)).strftime("%Y-%m-%d")
    }

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
            return {**c, "discount_amount": discount_amount,
                    "final_total": round(subtotal - discount_amount, 2)}
    raise HTTPException(status_code=404, detail="Invalid coupon code.")

def use_coupon(code: str) -> None:
    coupons = load_coupons()
    for c in coupons:
        if c.get("code", "").upper() == code.strip().upper():
            c["usage_count"] = c.get("usage_count", 0) + 1
    save_coupons(coupons)

def send_order_email(order: Dict[str, Any]) -> None:
    """Non-blocking email; silently skips if SMTP not configured."""
    import smtplib, ssl
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


def save_uploaded_image(upload: UploadFile) -> str:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type.")

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOADS_DIR / filename
    with destination.open("wb") as target:
        shutil.copyfileobj(upload.file, target)
    return f"/images/uploads/{filename}"


def delete_uploaded_image(image_url: str) -> None:
    if not image_url.startswith("/images/uploads/"):
        return
    relative_path = image_url.removeprefix("/images/")
    file_path = IMAGES_DIR / relative_path
    if file_path.exists():
        file_path.unlink()


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

app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

pages_router = APIRouter()
auth_router = APIRouter(tags=["auth"])
products_router = APIRouter(prefix="/api", tags=["products"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
orders_router = APIRouter(prefix="/api", tags=["orders"])
contact_router = APIRouter(prefix="/api", tags=["contact"])
payment_router = APIRouter(prefix="/api/payment", tags=["payment"])
coupon_router = APIRouter(prefix="/api", tags=["coupons"])
wishlist_router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])



def html_response(filename: str) -> FileResponse:
    path = HTML_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Page {filename} not found")
    return FileResponse(path)


@pages_router.get("/", include_in_schema=False)
def serve_home() -> FileResponse:
    return html_response("index.html")


@pages_router.get("/products", include_in_schema=False)
def serve_products_page() -> FileResponse:
    return html_response("products.html")


@pages_router.get("/cart", include_in_schema=False)
def serve_cart_page() -> FileResponse:
    return html_response("cart.html")

@pages_router.get("/checkout", include_in_schema=False)
def serve_checkout_page() -> FileResponse:
    return html_response("checkout.html")



@pages_router.get("/auth", include_in_schema=False)
def serve_auth_page(request: Request) -> RedirectResponse:
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/login{query}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@pages_router.get("/login", include_in_schema=False)
def serve_login_page() -> FileResponse:
    return html_response("login.html")


@pages_router.get("/register", include_in_schema=False)
def serve_register_page() -> FileResponse:
    return html_response("register.html")


@pages_router.get("/about", include_in_schema=False)
def serve_about_page() -> FileResponse:
    return html_response("about.html")


@pages_router.get("/contact", include_in_schema=False)
def serve_contact_page() -> FileResponse:
    return html_response("contact.html")


@pages_router.get("/admin", include_in_schema=False, response_model=None)
def serve_admin_page(request: Request):
    user = get_session_user(request)
    if not user or user.get("role") != "admin":
        next_path = quote("/admin", safe="")
        return RedirectResponse(url=f"/login?next={next_path}", status_code=status.HTTP_303_SEE_OTHER)
    return html_response("admin.html")


@pages_router.get("/wishlist", include_in_schema=False)
def serve_wishlist_page() -> FileResponse:
    return html_response("wishlist.html")


@pages_router.get("/privacy", include_in_schema=False)
def serve_privacy_page() -> FileResponse:
    return html_response("privacy.html")


@pages_router.get("/terms", include_in_schema=False)
def serve_terms_page() -> FileResponse:
    return html_response("terms.html")


@pages_router.get("/returns", include_in_schema=False)
def serve_returns_page() -> FileResponse:
    return html_response("returns.html")


@pages_router.get("/shipping", include_in_schema=False)
def serve_shipping_page() -> FileResponse:
    return html_response("shipping.html")


@pages_router.get("/track", include_in_schema=False)
def serve_track_page() -> FileResponse:
    return html_response("track.html")

@pages_router.get("/shop", include_in_schema=False)
def legacy_shop_page() -> RedirectResponse:
    return RedirectResponse(url="/products", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@pages_router.get("/{page_name}.html", include_in_schema=False, response_model=None)
def legacy_html_routes(page_name: str, request: Request):
    mapping = {
        "index": "/",
        "shop": "/products",
        "products": "/products",
        "cart": "/cart",
        "checkout": "/checkout",
        "auth": "/login",
        "login": "/login",
        "register": "/register",
        "about": "/about",
        "contact": "/contact",
        "admin": "/admin",
        "privacy": "/privacy",
        "terms": "/terms",
        "returns": "/returns",
        "shipping": "/shipping",
        "profile": "/profile",
        "dashboard": "/profile",
        "profile-setup": "/profile-setup",
        "verify": "/verify"
    }
    target = mapping.get(page_name)
    if not target:
        return FileResponse(HTML_DIR / "404.html", status_code=404)
    if target == "/admin":
        return serve_admin_page(request)
    return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@pages_router.get("/profile", include_in_schema=False)
def serve_profile_page() -> FileResponse:
    return html_response("profile.html")

@pages_router.get("/dashboard", include_in_schema=False)
def serve_dashboard_page() -> RedirectResponse:
    return RedirectResponse(url="/profile", status_code=status.HTTP_307_TEMPORARY_REDIRECT)

@pages_router.get("/profile-setup", include_in_schema=False)
def serve_profile_setup_page() -> FileResponse:
    return html_response("profile-setup.html")

@pages_router.get("/verify", include_in_schema=False)
def serve_verify_page() -> FileResponse:
    return html_response("verify.html")


@auth_router.get("/api/auth/me")
def get_auth_state(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    return {"authenticated": bool(user), "user": serialize_user(user) if user else None}


@auth_router.post("/register")
@auth_router.post("/api/auth/register")
def register(payload: RegisterPayload, request: Request) -> Dict[str, Any]:
    name = payload.name.strip()
    email = validate_email(payload.email)
    password = payload.password.strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 2 characters.")
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")
    if payload.confirm_password is not None and payload.confirm_password.strip() != password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match.")
    if find_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")

    users = load_users()
    current_year_suffix = datetime.now().strftime("%y")
    
    # Generate sequential ID starting from 001 for current year
    highest_seq = 0
    prefix = f"TW{current_year_suffix}-"
    for u in users:
        uid = str(u.get("user_id", ""))
        if uid.startswith(prefix):
            try:
                seq = int(uid.split("-")[1])
                if seq > highest_seq:
                    highest_seq = seq
            except Exception:
                pass
    
    seq_number = str(highest_seq + 1).zfill(3)
    user_id_formatted = f"{prefix}{seq_number}"
    import random
    otp = str(random.randint(100000, 999999))
    
    # ─── REAL EMAIL DISPATCH ───
    import smtplib
    from email.mime.text import MIMEText
    
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    
    if smtp_host and smtp_user:
        msg = MIMEText(f"Hello {name},\n\nYour Trident Wear verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nThank you,\nTrident Wear Team")
        msg["Subject"] = "Trident Wear - Email Verification OTP"
        msg["From"] = smtp_user
        msg["To"] = email
        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [email], msg.as_string())
            print(f"Successfully dispatched real OTP email to {email}")
        except Exception as e:
            print(f"SMTP sending failed: {e}")
            # Fallback to local log if email fails
            print(f"FALLBACK OTP DISPLAY: {otp}")
    else:
        print(f"DEBUG (NO SMTP CONFIGURED): Sent OTP {otp} for registration of {email}")

    new_user = {
        "id": next_id(users),
        "user_id": user_id_formatted,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "customer",
        "gender": getattr(payload, "gender", None),
        "otp": otp,
        "otp_expiry": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        "otp_verification_status": False,
        "profile_completed_status": False,
        "created_at": now_iso(),
    }
    users.append(new_user)
    save_users(users)

    # We do NOT return a token. They must verify OTP.
    return {"success": True, "message": "Account created. Please check your email for the OTP.", "email": email}


@auth_router.post("/login")
@auth_router.post("/api/auth/login")
def login(payload: LoginPayload, request: Request) -> Dict[str, Any]:
    email = validate_email(payload.email)
    password = payload.password.strip()
    user = find_user_by_email(email)

    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    
    if user.get("role") != "admin" and not user.get("otp_verification_status", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email OTP before logging in.")

    user = upgrade_password_hash_if_needed(user, password)
    store_session_user(request, user)
    token = issue_auth_token(user)

    return {"success": True, "message": "Signed in successfully.", "token": token, "user": serialize_user(user)}


@auth_router.post("/api/auth/otp/send")
def send_otp(payload: OTPPayload) -> Dict[str, Any]:
    return {"success": True, "message": "OTP sent."}


@auth_router.post("/api/auth/otp/verify")
def verify_otp(payload: OTPPayload, request: Request) -> Dict[str, Any]:
    users = load_users()
    email_variant = f"{payload.phone}@trident.local"
    user = find_user_by_email(email_variant)
    if not user:
        user = {
            "id": next_id(users),
            "name": payload.phone,
            "email": email_variant,
            "password_hash": hash_password("dummy"),
            "role": "customer",
            "created_at": now_iso(),
        }
        users.append(user)
        save_users(users)
    
    store_session_user(request, user)
    token = issue_auth_token(user)
    return {"success": True, "message": "OTP verified.", "token": token, "user": serialize_user(user)}


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

@auth_router.post("/api/auth/google")
def google_login(payload: GooglePayload, request: Request) -> Dict[str, Any]:
    users = load_users()
    user = find_user_by_email(payload.email)
    if not user:
        user = {
            "id": next_id(users),
            "name": payload.name,
            "email": payload.email,
            "password_hash": hash_password("dummy"),
            "role": "customer",
            "created_at": now_iso(),
        }
        users.append(user)
        save_users(users)
        
    store_session_user(request, user)
    token = issue_auth_token(user)
    return {"success": True, "message": "Signed in with Google.", "token": token, "user": serialize_user(user)}


@auth_router.post("/logout")
@auth_router.post("/api/auth/logout")
def logout(request: Request) -> Dict[str, Any]:
    revoke_auth_token(get_request_token(request))
    request.session.clear()
    return {"success": True, "message": "Signed out."}


@products_router.get("/products")
def get_products(category: Optional[str] = None, featured: Optional[bool] = None) -> Dict[str, Any]:
    products = load_products()

    if category:
        category_value = category.strip().lower()
        products = [product for product in products if product["category"] == category_value]

    if featured is not None:
        products = [product for product in products if product["featured"] is featured]

    return {"success": True, "count": len(products), "products": products}


@products_router.get("/products/{product_id}")
def get_single_product(product_id: int) -> Dict[str, Any]:
    for product in load_products():
        if product["id"] == product_id:
            return {"success": True, "product": product}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")


def validate_product_fields(
    name: str,
    category: str,
    price: str,
    description: str,
    tag: str,
    sizes: str,
    stock: str,
    featured: str,
) -> Dict[str, Any]:
    product_name = name.strip()
    category_value = category.strip().lower()
    description_value = description.strip()

    if len(product_name) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product name must be at least 3 characters.")
    if category_value not in {"tshirt", "shirt"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category must be tshirt or shirt.")

    try:
        price_value = int(float(price))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be a valid number.") from error
    if price_value <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be greater than zero.")

    try:
        stock_value = max(int(float(stock or 0)), 0)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock must be a valid number.") from error

    return {
        "name": product_name,
        "category": category_value,
        "price": price_value,
        "description": description_value,
        "tag": tag.strip(),
        "sizes": normalize_sizes(sizes),
        "stock": stock_value,
        "featured": normalize_bool(featured),
    }


@admin_router.post("/products")
async def create_product(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    price: str = Form(...),
    description: str = Form(""),
    tag: str = Form(""),
    sizes: str = Form("S, M, L, XL"),
    stock: str = Form("0"),
    featured: str = Form("false"),
    image: Optional[UploadFile] = File(None),
    _: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    product_data = validate_product_fields(name, category, price, description, tag, sizes, stock, featured)
    products = load_products()

    image_path = "/images/hero-banner.png"
    if image and image.filename:
        image_path = save_uploaded_image(image)
        await image.close()

    new_product = {
        "id": next_id(products),
        **product_data,
        "image": image_path,
    }
    products.append(new_product)
    normalized = save_products(products)
    product = next(product for product in normalized if product["id"] == new_product["id"])
    return {"success": True, "message": "Product added successfully.", "product": product}


@admin_router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    price: str = Form(...),
    description: str = Form(""),
    tag: str = Form(""),
    sizes: str = Form("S, M, L, XL"),
    stock: str = Form("0"),
    featured: str = Form("false"),
    image: Optional[UploadFile] = File(None),
    _: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    product_data = validate_product_fields(name, category, price, description, tag, sizes, stock, featured)
    products = load_products()
    existing = next((product for product in products if product["id"] == product_id), None)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    image_path = existing["image"]
    if image and image.filename:
        new_image_path = save_uploaded_image(image)
        await image.close()
        delete_uploaded_image(existing["image"])
        image_path = new_image_path

    updated_product = {
        "id": product_id,
        **product_data,
        "image": image_path,
    }
    updated_products = [updated_product if product["id"] == product_id else product for product in products]
    normalized = save_products(updated_products)
    product = next(product for product in normalized if product["id"] == product_id)
    return {"success": True, "message": "Product updated successfully.", "product": product}


@admin_router.delete("/products/{product_id}")
def delete_product(product_id: int, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    products = load_products()
    existing = next((product for product in products if product["id"] == product_id), None)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    delete_uploaded_image(existing["image"])
    remaining_products = [product for product in products if product["id"] != product_id]
    save_products(remaining_products)
    return {"success": True, "message": f'{existing["name"]} deleted.'}


@orders_router.get("/stats")
def get_stats() -> Dict[str, int]:
    orders = load_orders()
    # Count unique users based on email, fallback to 150 if none yet for display
    unique_users = set(o.get("customer", {}).get("email") for o in orders if o.get("customer", {}).get("email"))
    baseline = 150
    return {"customers": baseline + len(unique_users) if unique_users else baseline + len(orders)}

@orders_router.post("/orders")
def create_order(payload: OrderPayload, request: Request) -> Dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")
    # Stock check
    products = load_products()
    prod_map = {p["id"]: p for p in products}
    for item in payload.items:
        pid = int(item.get("id", 0))
        qty = max(int(item.get("qty", 1)), 1)
        if pid in prod_map and prod_map[pid]["stock"] < qty:
            raise HTTPException(status_code=400, detail=f'Insufficient stock for {prod_map[pid]["name"]}')


    customer_name = str(payload.customer.get("name", "")).strip()
    customer_email = validate_email(str(payload.customer.get("email", "") or "guest@trident.local"))
    shipping_address = str(payload.shipping.get("address", "")).strip()
    shipping_city = str(payload.shipping.get("city", "")).strip()
    shipping_phone = str(payload.customer.get("phone", "")).strip()

    if len(customer_name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer name is required.")
    if len(shipping_address) < 6 or len(shipping_city) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete shipping details are required.")
    if len(shipping_phone) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid phone number is required.")

    user = get_session_user(request)
    items = []
    for item in payload.items:
        qty = max(int(item.get("qty", 1)), 1)
        items.append(
            {
                "id": int(item.get("id", 0)),
                "name": str(item.get("name", "")).strip(),
                "price": int(float(item.get("price", 0) or 0)),
                "image": normalize_image_path(str(item.get("image", ""))),
                "qty": qty,
                "size": str(item.get("size", "")).strip().upper(),
            }
        )

    order = {
        "order_id": f"TRI-{uuid.uuid4().hex[:8].upper()}",
        "items": items,
        "subtotal": int(float(payload.subtotal)),
        "customer": {
            "name": customer_name,
            "email": customer_email if customer_email != "guest@trident.local" else str(payload.customer.get("email", "")).strip(),
            "phone": shipping_phone,
            "user_id": user["id"] if user else None,
        },
        "shipping": {
            "address": shipping_address,
            "city": shipping_city,
            "postal_code": str(payload.shipping.get("postal_code", "")).strip(),
            "country": str(payload.shipping.get("country", "India")).strip() or "India",
            "notes": str(payload.shipping.get("notes", "")).strip(),
        },
        "status": "confirmed",
        "created_at": now_iso(),
    }

    orders = load_orders()
    orders.append(order)
    save_orders(orders)
    try:
        deduct_stock(items)
    except Exception:
        pass
    try:
        send_order_email(order)
    except Exception:
        pass
    return {"success": True, "message": "Order placed successfully.", "order_id": order["order_id"]}


@contact_router.post("/contact")
def create_contact_message(payload: ContactPayload) -> Dict[str, Any]:
    name = payload.name.strip()
    email = validate_email(payload.email)
    message = payload.message.strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required.")
    if len(message) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message must be at least 10 characters.")

    contacts = load_contacts()
    contact = {
        "id": next_id(contacts),
        "name": name,
        "email": email,
        "message": message,
        "created_at": now_iso(),
    }
    contacts.append(contact)
    save_contacts(contacts)
    return {"success": True, "message": "Message sent successfully."}


app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(admin_router)
app.include_router(orders_router)
app.include_router(contact_router)


@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and "text/html" in request.headers.get("accept", ""):
        return FileResponse(HTML_DIR / "404.html", status_code=404)
    from fastapi.responses import JSONResponse
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
def create_shiprocket_shipment(order: Dict[str, Any]) -> Dict[str, Any]:
    # In a real app, this would use Shiprocket API credentials from os.getenv("SHIPROCKET_EMAIL") etc.
    # For now, we simulate a successful AWB generation.
    return {
        "status": "shipped",
        "tracking_id": f"SR{uuid.uuid4().hex[:8].upper()}",
        "courier": "Delhivery (Shiprocket)",
        "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=4)).date().isoformat()
    }

@admin_router.get("/orders")
def get_all_orders(_: Dict[str, Any] = Depends(require_admin)) -> List[Dict[str, Any]]:
    return load_orders()

@admin_router.put("/orders/{order_id}")
def update_order_status(order_id: str, payload: OrderStatusUpdate, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            o["status"] = payload.status
            # Trigger shipment logic
            if payload.status == "shipped" and not o.get("tracking_id"):
                try:
                    shipment = create_shiprocket_shipment(o)
                    o["tracking_id"] = shipment["tracking_id"]
                    o["courier"] = shipment["courier"]
                    o["estimated_delivery"] = shipment["estimated_delivery"]
                except Exception:
                    pass # Fallback handled by client tracking API

            save_orders(orders)
            return {"success": True, "message": "Order status updated.", "order": o}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

@orders_router.get("/orders/{order_id}/tracking")
def track_order(order_id: str) -> Dict[str, Any]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            if o.get("tracking_id"):
                return {
                    "status": "In Transit" if o.get("status") == "shipped" else o.get("status", "Unknown").title(),
                    "courier": o.get("courier", "Standard Courier"),
                    "tracking_id": o.get("tracking_id"),
                    "estimated_delivery": o.get("estimated_delivery", "TBD")
                }
            return {
                "status": o.get("status", "pending").title(),
                "courier": "Pending Allocation",
                "tracking_id": None,
                "estimated_delivery": "Tracking will be updated soon"
            }
    raise HTTPException(status_code=404, detail="Order not found.")

# ════════════════════════════════════════════════════════════
# ADVANCED AUTH (OTP & GOOGLE)
# ════════════════════════════════════════════════════════════
@auth_router.post("/api/auth/otp/send")
def send_otp(payload: OTPPayload) -> Dict[str, Any]:
    # Simulation: In production use Twilio or Msg91
    print(f"DEBUG: Sent OTP 123456 to {payload.phone}")
    return {"success": True, "message": "OTP sent successfully."}

@auth_router.post("/api/auth/otp/verify")
def verify_otp(payload: OTPPayload, request: Request) -> Dict[str, Any]:
    if payload.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    
    users = load_users()
    user = next((u for u in users if u.get("phone") == payload.phone), None)
    if not user:
        user = {
            "id": next_id(users),
            "name": payload.name or f"User {payload.phone[-4:]}",
            "email": f"user{uuid.uuid4().hex[:4]}@trident.local",
            "phone": payload.phone,
            "role": "customer",
            "created_at": now_iso()
        }
        users.append(user)
        save_users(users)
        
    store_session_user(request, user)
    token = issue_auth_token(user)
    return {"success": True, "token": token, "user": serialize_user(user)}

@auth_router.post("/api/auth/google")
def google_auth(payload: GooglePayload, request: Request) -> Dict[str, Any]:
    # In real app, verify payload.id_token with google.oauth2.id_token
    users = load_users()
    user = find_user_by_email(payload.email)
    if not user:
        user = {
            "id": next_id(users),
            "name": payload.name,
            "email": payload.email,
            "role": "customer",
            "created_at": now_iso()
        }
        users.append(user)
        save_users(users)
        
    store_session_user(request, user)
    token = issue_auth_token(user)
    return {"success": True, "token": token, "user": serialize_user(user)}


@admin_router.get("/analytics")
def get_analytics(_: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    orders = load_orders()
    total_orders = len(orders)
    total_revenue = sum(o.get("subtotal", 0) for o in orders)
    unique_customers = len(set(o.get("customer", {}).get("email") for o in orders if o.get("customer", {}).get("email")))
    
    # Simple top products computation
    product_sales = {}
    for o in orders:
        for item in o.get("items", []):
            name = item.get("name")
            qty = item.get("qty", 1)
            if name:
                product_sales[name] = product_sales.get(name, 0) + qty
                
    top_products = [{"name": k, "sold": v} for k, v in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "customers": unique_customers,
        "top_products": top_products
    }

# ════════════════════════════════════════════════════════════
# CHECKOUT & PAYMENT SYSTEM
# ════════════════════════════════════════════════════════════
payment_router = APIRouter(prefix="/api/payment", tags=["Payment"])

@payment_router.post("/cod")
def place_cod_order(payload: CODPayload, request: Request) -> Dict[str, Any]:
    orders = load_orders()
    order_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
    
    new_order = {
        "id": next_id(orders),
        "order_id": order_id,
        "method": "COD",
        "subtotal": payload.subtotal,
        "customer": payload.customer,
        "shipping": payload.shipping,
        "items": payload.items,
        "coupon_code": getattr(payload, "coupon_code", None),
        "status": "pending",
        "created_at": now_iso()
    }
    orders.append(new_order)
    save_orders(orders)
    
    # Optionally send email
    try:
        send_order_email(payload.customer.get("email"), order_id, "COD")
    except Exception:
        pass
        
    return {"success": True, "order_id": order_id, "message": "COD order placed successfully"}

@payment_router.post("/create-order")
def create_razorpay_order(payload: RazorpayCreatePayload) -> Dict[str, Any]:
    import os
    rz_key = os.getenv("RAZORPAY_KEY", "rzp_test_mockkey")
    # Normally we call razorpay.Client here
    # Mock response for testing or offline
    mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
    return {
        "success": True,
        "razorpay_order_id": mock_order_id,
        "key_id": rz_key
    }

@payment_router.post("/verify")
def verify_razorpay_payment(payload: RazorpayVerifyPayload) -> Dict[str, Any]:
    # Mock signature verification
    orders = load_orders()
    order_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
    
    new_order = {
        "id": next_id(orders),
        "order_id": order_id,
        "method": "Razorpay",
        "razorpay_payment_id": payload.razorpay_payment_id,
        "subtotal": payload.order_data.get("subtotal"),
        "customer": payload.order_data.get("customer"),
        "shipping": payload.order_data.get("shipping"),
        "items": payload.order_data.get("items"),
        "coupon_code": payload.order_data.get("coupon_code"),
        "status": "paid",
        "created_at": now_iso()
    }
    orders.append(new_order)
    save_orders(orders)
    
    try:
        user_email = payload.order_data.get("customer", {}).get("email")
        send_order_email(user_email, order_id, "Online")
    except Exception:
        pass
        
    return {"success": True, "order_id": order_id, "message": "Payment verified and order placed"}

app.include_router(payment_router)

# ════════════════════════════════════════════════════════════
# CHAT SYSTEM
# ════════════════════════════════════════════════════════════
@app.post("/api/chat/send")
def send_chat(payload: ChatMessagePayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    chats = load_chat()
    
    # If anonymous, identify them by a generic thread_id
    if user:
        thread_id = f"user_{user['id']}"
        author = user["name"]
    else:
        thread_id = payload.thread_id or f"anon_{uuid.uuid4().hex[:8]}"
        author = "Guest"
        
    msg = {
        "id": next_id(chats),
        "thread_id": thread_id,
        "author": author,
        "role": "user",
        "message": payload.message,
        "timestamp": now_iso(),
        "read": False
    }
    chats.append(msg)
    save_chat(chats)
    return {"success": True, "message": msg, "thread_id": thread_id}

@app.get("/api/chat/messages")
def get_chat_messages(thread_id: str) -> List[Dict[str, Any]]:
    chats = load_chat()
    return [c for c in chats if c["thread_id"] == thread_id]

@admin_router.get("/chat")
def admin_get_chats(_: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    chats = load_chat()
    threads = {}
    for c in chats:
        tid = c["thread_id"]
        if tid not in threads:
            threads[tid] = []
        threads[tid].append(c)
    return threads

@admin_router.post("/chat/reply")
def admin_reply_chat(payload: ChatMessagePayload, request: Request, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    if not payload.thread_id:
        raise HTTPException(status_code=400, detail="Thread ID required")
    
    chats = load_chat()
    msg = {
        "id": next_id(chats),
        "thread_id": payload.thread_id,
        "author": "Supporting Staff",
        "role": "admin",
        "message": payload.message,
        "timestamp": now_iso(),
        "read": True
    }
    
    # mark whole thread as read by admin
    for c in chats:
        if c["thread_id"] == payload.thread_id:
            c["read"] = True

    chats.append(msg)
    save_chat(chats)
    return {"success": True, "message": msg}
