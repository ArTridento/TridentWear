from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
HTML_DIR = FRONTEND_DIR / "html"
CSS_DIR = FRONTEND_DIR / "css"
JS_DIR = FRONTEND_DIR / "js"
IMAGES_DIR = FRONTEND_DIR / "images"
UPLOADS_DIR = IMAGES_DIR / "uploads"

DB_DIR = BASE_DIR / "db"
PRODUCTS_PATH = DB_DIR / "products.json"
ORDERS_PATH = DB_DIR / "orders.json"
USERS_PATH = DB_DIR / "users.json"
CONTACTS_PATH = DB_DIR / "contacts.json"
FRONTEND_PRODUCTS_PATH = JS_DIR / "products.json"

PASSWORD_ITERATIONS = 120_000
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class RegisterPayload(BaseModel):
    name: str
    email: str
    password: str


class LoginPayload(BaseModel):
    email: str
    password: str


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
        "description": "Oversized drop-shoulder tee in charcoal grey. Heavy cotton weight with a premium streetwear drape.",
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
    "password_hash": "pbkdf2_sha256$120000$dHJpZGVudC1hZG1pbi1zYWx0$u18gS+1HGVISRBv+6SO4YQRt0VWUGQqny6zPVDTTePk=",
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


def load_users() -> List[Dict[str, Any]]:
    return read_json(USERS_PATH, [DEFAULT_ADMIN])


def save_users(users: List[Dict[str, Any]]) -> None:
    write_json(USERS_PATH, users)


def load_contacts() -> List[Dict[str, Any]]:
    return read_json(CONTACTS_PATH, [])


def save_contacts(contacts: List[Dict[str, Any]]) -> None:
    write_json(CONTACTS_PATH, contacts)


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
    salt_bytes = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, PASSWORD_ITERATIONS)
    salt_encoded = base64.b64encode(salt_bytes).decode("utf-8")
    digest_encoded = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt_encoded}${digest_encoded}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_encoded, digest_encoded = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_text)
        salt_bytes = base64.b64decode(salt_encoded.encode("utf-8"))
    except (ValueError, TypeError):
        return False

    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations)
    expected = base64.b64decode(digest_encoded.encode("utf-8"))
    return hmac.compare_digest(computed, expected)


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    target = email.strip().lower()
    for user in load_users():
        if user.get("email", "").lower() == target:
            return user
    return None


def get_session_user(request: Request) -> Optional[Dict[str, Any]]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    for user in load_users():
        if int(user.get("id", 0)) == int(user_id):
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
    if "@" not in normalized or "." not in normalized.split("@")[-1]:
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


app = FastAPI(title="Trident Premium Store")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("TRIDENT_SESSION_SECRET", "trident-local-session-secret"),
    same_site="lax",
    https_only=False,
)

ensure_data_files()

app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

pages_router = APIRouter()
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
products_router = APIRouter(prefix="/api", tags=["products"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])
orders_router = APIRouter(prefix="/api", tags=["orders"])
contact_router = APIRouter(prefix="/api", tags=["contact"])


def html_response(filename: str) -> FileResponse:
    return FileResponse(HTML_DIR / filename)


@pages_router.get("/", include_in_schema=False)
def serve_home() -> FileResponse:
    return html_response("index.html")


@pages_router.get("/products", include_in_schema=False)
def serve_products_page() -> FileResponse:
    return html_response("shop.html")


@pages_router.get("/product", include_in_schema=False)
def serve_product_page() -> FileResponse:
    return html_response("product.html")


@pages_router.get("/cart", include_in_schema=False)
def serve_cart_page() -> FileResponse:
    return html_response("cart.html")


@pages_router.get("/auth", include_in_schema=False)
def serve_auth_page() -> FileResponse:
    return html_response("auth.html")


@pages_router.get("/about", include_in_schema=False)
def serve_about_page() -> FileResponse:
    return html_response("about.html")


@pages_router.get("/contact", include_in_schema=False)
def serve_contact_page() -> FileResponse:
    return html_response("contact.html")


@pages_router.get("/admin", include_in_schema=False)
def serve_admin_page(request: Request) -> FileResponse | RedirectResponse:
    user = get_session_user(request)
    if not user or user.get("role") != "admin":
        next_path = quote("/admin", safe="")
        return RedirectResponse(url=f"/auth?next={next_path}", status_code=status.HTTP_303_SEE_OTHER)
    return html_response("admin.html")


@pages_router.get("/shop", include_in_schema=False)
def legacy_shop_page() -> RedirectResponse:
    return RedirectResponse(url="/products", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@pages_router.get("/{page_name}.html", include_in_schema=False)
def legacy_html_routes(page_name: str, request: Request) -> FileResponse | RedirectResponse:
    mapping = {
        "index": "/",
        "shop": "/products",
        "products": "/products",
        "product": "/product",
        "cart": "/cart",
        "auth": "/auth",
        "about": "/about",
        "contact": "/contact",
        "admin": "/admin",
    }
    target = mapping.get(page_name)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found.")
    if target == "/admin":
        return serve_admin_page(request)
    if target in {"/", "/products", "/product", "/cart", "/auth", "/about", "/contact"}:
        return html_response(f"{'index' if target == '/' else target.removeprefix('/')}.html" if target != "/products" else "shop.html")
    return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/me")
def get_auth_state(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    return {"authenticated": bool(user), "user": serialize_user(user) if user else None}


@auth_router.post("/register")
def register(payload: RegisterPayload, request: Request) -> Dict[str, Any]:
    name = payload.name.strip()
    email = validate_email(payload.email)
    password = payload.password.strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 2 characters.")
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")
    if find_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")

    users = load_users()
    new_user = {
        "id": next_id(users),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "customer",
        "created_at": now_iso(),
    }
    users.append(new_user)
    save_users(users)

    request.session.clear()
    request.session["user_id"] = new_user["id"]

    return {"success": True, "message": "Account created successfully.", "user": serialize_user(new_user)}


@auth_router.post("/login")
def login(payload: LoginPayload, request: Request) -> Dict[str, Any]:
    email = validate_email(payload.email)
    password = payload.password.strip()
    user = find_user_by_email(email)

    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    request.session.clear()
    request.session["user_id"] = user["id"]

    return {"success": True, "message": "Signed in successfully.", "user": serialize_user(user)}


@auth_router.post("/logout")
def logout(request: Request) -> Dict[str, Any]:
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


@orders_router.post("/orders")
def create_order(payload: OrderPayload, request: Request) -> Dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")

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
