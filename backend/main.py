from __future__ import annotations

import base64
import hashlib
import hmac
import mimetypes
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
HTML_DIR = FRONTEND_DIR / "html"
CSS_DIR = FRONTEND_DIR / "css"
JS_DIR = FRONTEND_DIR / "js"
IMAGES_DIR = FRONTEND_DIR / "images"

DEFAULT_IMAGE = "/images/hero-banner.png"
DEFAULT_SIZES = ["S", "M", "L", "XL", "XXL"]
DEFAULT_CATEGORY = "tshirt"
DEFAULT_FIT = "Regular Fit"
DEFAULT_NECK = "Round Neck"
DEFAULT_MATERIAL = "Cotton"
DEFAULT_GSM = 220
DEFAULT_DESIGN = "Plain"
DEFAULT_SPECIAL = ""
ADMIN_EMAIL = "admin@trident.local"
ADMIN_PASSWORD = "TridentAdmin123!"


class ProductBase(BaseModel):
    name: str
    price: float
    image: str = DEFAULT_IMAGE
    description: str
    category: str = DEFAULT_CATEGORY
    categories: list[str] = Field(default_factory=lambda: ["regular-fit", "round-neck", "cotton", "plain"])
    material: str = DEFAULT_MATERIAL
    gsm: int = DEFAULT_GSM
    fit_type: str = DEFAULT_FIT
    neck_type: str = DEFAULT_NECK
    design_type: str = DEFAULT_DESIGN
    special_type: str = DEFAULT_SPECIAL
    tag: str = "New Arrival"
    sizes: list[str] = Field(default_factory=lambda: DEFAULT_SIZES.copy())
    stock: int = 25
    featured: bool = False


class Product(ProductBase):
    id: int


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


class CartItem(BaseModel):
    id: int
    name: str
    price: float
    image: str
    qty: int = 1
    size: str = "M"


class CustomerPayload(BaseModel):
    name: str
    email: str
    phone: str


class ShippingPayload(BaseModel):
    address: str
    city: str
    postal_code: str = ""
    country: str = "India"
    notes: str = ""


class OrderPayload(BaseModel):
    items: list[CartItem]
    subtotal: float
    customer: CustomerPayload
    shipping: ShippingPayload


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    normalized = str(value or "").strip().lower()
    for source, target in {"&": "and", "/": " ", "_": " "}.items():
        normalized = normalized.replace(source, target)
    return "-".join(part for part in normalized.replace("  ", " ").split() if part)


def title_or_default(value: Any, default: str) -> str:
    cleaned = str(value or "").strip()
    return cleaned or default


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), stored_hash)


def validate_email(value: str) -> str:
    email = str(value or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address.")
    return email


def normalize_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def normalize_sizes(value: Any) -> list[str]:
    if isinstance(value, list):
        sizes = [str(size).strip().upper() for size in value if str(size).strip()]
    else:
        sizes = [part.strip().upper() for part in str(value or "").split(",") if part.strip()]
    return sizes or DEFAULT_SIZES.copy()


def normalize_image_path(value: str) -> str:
    image = str(value or "").strip()
    if not image:
        return DEFAULT_IMAGE
    if image.startswith(("data:", "http://", "https://", "/images/")):
        return image
    return f"/images/{Path(image).name}"


def derive_categories(
    fit_type: str,
    neck_type: str,
    material: str,
    design_type: str,
    special_type: str,
    raw_categories: Any = None,
) -> list[str]:
    categories: list[str] = []

    if isinstance(raw_categories, list):
        categories.extend(slugify(category) for category in raw_categories if str(category).strip())
    elif str(raw_categories or "").strip():
        categories.extend(slugify(category) for category in str(raw_categories).split(",") if str(category).strip())

    categories.extend([slugify(fit_type), slugify(neck_type), slugify(material), slugify(design_type)])

    if str(special_type or "").strip():
        categories.append(slugify(special_type))

    unique: list[str] = []
    for category in categories:
        if category and category not in unique:
            unique.append(category)
    return unique


def product_seed() -> list[dict[str, Any]]:
    return [
        {
            "id": 1,
            "name": "Core Regular Tee",
            "price": 699,
            "description": "Clean everyday T-shirt with a soft handfeel, easy drape, and a balanced regular silhouette.",
            "image": "/images/white-tshirt.png",
            "fit_type": "Regular Fit",
            "neck_type": "Round Neck",
            "material": "Cotton",
            "gsm": 180,
            "design_type": "Plain",
            "special_type": "",
            "tag": "Everyday Core",
            "sizes": DEFAULT_SIZES,
            "stock": 160,
            "featured": True,
        },
        {
            "id": 2,
            "name": "Contour Slim V Tee",
            "price": 799,
            "description": "Sharper slim silhouette with a neat V-neck finish and a cotton blend built for a close fit.",
            "image": "/images/white-tshirt.png",
            "fit_type": "Slim Fit",
            "neck_type": "V-Neck",
            "material": "Cotton Blend",
            "gsm": 200,
            "design_type": "Plain",
            "special_type": "",
            "tag": "Clean Cut",
            "sizes": DEFAULT_SIZES,
            "stock": 120,
            "featured": False,
        },
        {
            "id": 3,
            "name": "Archive Oversized Graphic Tee",
            "price": 1099,
            "description": "Heavy oversized tee with drop-shoulder construction and a large front graphic for a bold profile.",
            "image": "/images/grey-tshirt.png",
            "fit_type": "Oversized Fit",
            "neck_type": "Round Neck",
            "material": "Cotton",
            "gsm": 240,
            "design_type": "Graphic",
            "special_type": "Drop Shoulder",
            "tag": "Heavyweight",
            "sizes": DEFAULT_SIZES,
            "stock": 90,
            "featured": True,
        },
        {
            "id": 4,
            "name": "Frame Boxy Typography Tee",
            "price": 999,
            "description": "Boxy body with compact length, crisp sleeves, and clean typography graphics across the chest.",
            "image": "/images/black-tshirt.png",
            "fit_type": "Boxy Fit",
            "neck_type": "Round Neck",
            "material": "Cotton",
            "gsm": 220,
            "design_type": "Typography",
            "special_type": "",
            "tag": "Statement Type",
            "sizes": DEFAULT_SIZES,
            "stock": 110,
            "featured": True,
        },
        {
            "id": 5,
            "name": "Club Polo Tee",
            "price": 1199,
            "description": "Polo-collar T-shirt with a neat placket, soft blend yarn, and a refined everyday finish.",
            "image": "/images/olive-shirt.png",
            "fit_type": "Regular Fit",
            "neck_type": "Polo",
            "material": "Cotton Blend",
            "gsm": 220,
            "design_type": "Plain",
            "special_type": "",
            "tag": "Smart Casual",
            "sizes": DEFAULT_SIZES,
            "stock": 80,
            "featured": True,
        },
        {
            "id": 6,
            "name": "Motion Print Performance Tee",
            "price": 899,
            "description": "Light polyester performance tee with printed detailing and a close slim shape for active styling.",
            "image": "/images/white-tshirt.png",
            "fit_type": "Slim Fit",
            "neck_type": "Round Neck",
            "material": "Polyester",
            "gsm": 180,
            "design_type": "Printed",
            "special_type": "",
            "tag": "Performance",
            "sizes": DEFAULT_SIZES,
            "stock": 140,
            "featured": False,
        },
        {
            "id": 7,
            "name": "Studio Custom Print Tee",
            "price": 949,
            "description": "A made-for-graphics base tee with a smooth cotton face that shows custom artwork clearly.",
            "image": "/images/black-tshirt.png",
            "fit_type": "Regular Fit",
            "neck_type": "Round Neck",
            "material": "Cotton",
            "gsm": 200,
            "design_type": "Custom Print",
            "special_type": "",
            "tag": "Made To Print",
            "sizes": DEFAULT_SIZES,
            "stock": 95,
            "featured": False,
        },
        {
            "id": 8,
            "name": "Full Sleeve Minimal Tee",
            "price": 1099,
            "description": "Full sleeve silhouette with a clean front, denser cotton feel, and easy year-round layering.",
            "image": "/images/black-tshirt.png",
            "fit_type": "Regular Fit",
            "neck_type": "Round Neck",
            "material": "Cotton",
            "gsm": 220,
            "design_type": "Plain",
            "special_type": "Full Sleeve",
            "tag": "Layer Ready",
            "sizes": DEFAULT_SIZES,
            "stock": 75,
            "featured": False,
        },
        {
            "id": 9,
            "name": "Crop Graphic Tee",
            "price": 899,
            "description": "Shorter crop length with a graphic front, relaxed shoulders, and a soft cotton blend construction.",
            "image": "/images/grey-tshirt.png",
            "fit_type": "Boxy Fit",
            "neck_type": "Round Neck",
            "material": "Cotton Blend",
            "gsm": 200,
            "design_type": "Graphic",
            "special_type": "Crop",
            "tag": "Short Cut",
            "sizes": DEFAULT_SIZES,
            "stock": 70,
            "featured": False,
        },
        {
            "id": 10,
            "name": "Printed V Layer Tee",
            "price": 849,
            "description": "Printed V-neck tee in lightweight polyester, made for easy layering and quick-dry comfort.",
            "image": "/images/white-tshirt.png",
            "fit_type": "Slim Fit",
            "neck_type": "V-Neck",
            "material": "Polyester",
            "gsm": 180,
            "design_type": "Printed",
            "special_type": "",
            "tag": "Lightweight",
            "sizes": DEFAULT_SIZES,
            "stock": 115,
            "featured": False,
        },
    ]


def normalize_product(raw_product: dict[str, Any], index: int = 0) -> dict[str, Any]:
    fit_type = title_or_default(raw_product.get("fit_type"), DEFAULT_FIT)
    neck_type = title_or_default(raw_product.get("neck_type"), DEFAULT_NECK)
    material = title_or_default(raw_product.get("material"), DEFAULT_MATERIAL)
    design_type = title_or_default(raw_product.get("design_type"), DEFAULT_DESIGN)
    special_type = title_or_default(raw_product.get("special_type"), DEFAULT_SPECIAL)

    return Product(
        id=int(raw_product.get("id", index + 1)),
        name=title_or_default(raw_product.get("name"), f"TridentWear Tee {index + 1}"),
        price=max(float(raw_product.get("price", 0) or 0), 0),
        image=normalize_image_path(str(raw_product.get("image", ""))),
        description=title_or_default(raw_product.get("description"), "A versatile TridentWear T-shirt."),
        category=DEFAULT_CATEGORY,
        categories=derive_categories(
            fit_type=fit_type,
            neck_type=neck_type,
            material=material,
            design_type=design_type,
            special_type=special_type,
            raw_categories=raw_product.get("categories"),
        ),
        material=material,
        gsm=max(int(float(raw_product.get("gsm", DEFAULT_GSM) or DEFAULT_GSM)), 120),
        fit_type=fit_type,
        neck_type=neck_type,
        design_type=design_type,
        special_type=special_type,
        tag=title_or_default(raw_product.get("tag"), "New Arrival"),
        sizes=normalize_sizes(raw_product.get("sizes", DEFAULT_SIZES)),
        stock=max(int(float(raw_product.get("stock", 0) or 0)), 0),
        featured=normalize_bool(raw_product.get("featured"), index < 4),
    ).model_dump()


def serialize_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": user["created_at"],
    }


def next_id(items: list[dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(item.get("id", 0)) for item in items) + 1


def html_response(filename: str) -> FileResponse:
    file_path = HTML_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{filename} not found.")
    return FileResponse(file_path)


def wants_html(request: Request, response_format: str | None = None) -> bool:
    accept_header = request.headers.get("accept", "")
    return response_format != "json" and "text/html" in accept_header


async def image_to_data_url(upload: UploadFile) -> str:
    content = await upload.read()
    await upload.close()
    mime_type = upload.content_type or mimetypes.guess_type(upload.filename or "")[0] or "application/octet-stream"
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def find_user_by_email(email: str) -> dict[str, Any] | None:
    target = email.strip().lower()
    return next((user for user in USERS if user["email"] == target), None)


def get_session_token(request: Request) -> str | None:
    header_token = request.headers.get("x-session-token", "").strip()
    if header_token:
        return header_token

    auth_header = request.headers.get("authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return None


def get_current_user(request: Request) -> dict[str, Any] | None:
    token = get_session_token(request)
    if not token:
        return None

    user_id = SESSIONS.get(token)
    if not user_id:
        return None

    return next((user for user in USERS if user["id"] == user_id), None)


def require_current_user(request: Request) -> dict[str, Any]:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in first.")
    return user


def require_admin(request: Request) -> dict[str, Any]:
    user = require_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def create_session(user: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user["id"]
    return token


def filter_products(category: str | None = None, featured: bool | None = None) -> list[dict[str, Any]]:
    items = [product.copy() for product in PRODUCTS]
    if category:
        category_value = slugify(category)
        items = [
            product
            for product in items
            if category_value == slugify(product.get("category", "")) or category_value in product.get("categories", [])
        ]
    if featured is not None:
        items = [product for product in items if product["featured"] is featured]
    return items


def get_product_by_id(product_id: int) -> dict[str, Any] | None:
    return next((product for product in PRODUCTS if product["id"] == product_id), None)


def validate_product_payload(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    name = title_or_default(payload.get("name"), existing["name"] if existing else "")
    description = title_or_default(payload.get("description"), existing["description"] if existing else "")
    image = normalize_image_path(str(payload.get("image", existing["image"] if existing else DEFAULT_IMAGE)))
    fit_type = title_or_default(payload.get("fit_type"), existing["fit_type"] if existing else DEFAULT_FIT)
    neck_type = title_or_default(payload.get("neck_type"), existing["neck_type"] if existing else DEFAULT_NECK)
    material = title_or_default(payload.get("material"), existing["material"] if existing else DEFAULT_MATERIAL)
    design_type = title_or_default(payload.get("design_type"), existing["design_type"] if existing else DEFAULT_DESIGN)
    special_type = title_or_default(payload.get("special_type"), existing["special_type"] if existing else DEFAULT_SPECIAL)
    tag = title_or_default(payload.get("tag"), existing["tag"] if existing else "New Arrival")
    sizes = normalize_sizes(payload.get("sizes", existing["sizes"] if existing else DEFAULT_SIZES))
    featured = normalize_bool(payload.get("featured"), existing["featured"] if existing else False)

    if len(name) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product name must be at least 3 characters.")

    if len(description) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description must be at least 10 characters.")

    try:
        price = float(payload.get("price", existing["price"] if existing else 0))
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be a valid number.") from error

    try:
        stock = int(float(payload.get("stock", existing["stock"] if existing else 25)))
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock must be a valid number.") from error

    try:
        gsm = int(float(payload.get("gsm", existing["gsm"] if existing else DEFAULT_GSM)))
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GSM must be a valid number.") from error

    if price <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be greater than zero.")

    return {
        "name": name,
        "price": int(price),
        "image": image,
        "description": description,
        "category": DEFAULT_CATEGORY,
        "categories": derive_categories(
            fit_type=fit_type,
            neck_type=neck_type,
            material=material,
            design_type=design_type,
            special_type=special_type,
            raw_categories=payload.get("categories", existing["categories"] if existing else None),
        ),
        "material": material,
        "gsm": max(gsm, 120),
        "fit_type": fit_type,
        "neck_type": neck_type,
        "design_type": design_type,
        "special_type": special_type,
        "tag": tag,
        "sizes": sizes,
        "stock": max(stock, 0),
        "featured": featured,
    }


async def parse_product_submission(request: Request, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    raw_payload: dict[str, Any]

    if "application/json" in content_type:
        raw_payload = dict(await request.json())
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        raw_payload = {key: value for key, value in form.items()}
        image_value = form.get("image")
        if isinstance(image_value, UploadFile) and image_value.filename:
            raw_payload["image"] = await image_to_data_url(image_value)
        elif existing:
            raw_payload["image"] = existing["image"]
    else:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported request type.")

    return validate_product_payload(raw_payload, existing=existing)


app = FastAPI(title="TridentWear API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

PRODUCTS: list[dict[str, Any]] = [normalize_product(product, index) for index, product in enumerate(product_seed())]
USERS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "TridentWear Admin",
        "email": ADMIN_EMAIL,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "role": "admin",
        "created_at": now_iso(),
    }
]
SESSIONS: dict[str, int] = {}
ORDERS: list[dict[str, Any]] = []
CONTACTS: list[dict[str, Any]] = []


@app.get("/", include_in_schema=False, response_model=None)
def read_root(request: Request, format: str | None = Query(default=None)):
    if wants_html(request, format):
        return html_response("index.html")
    return PlainTextResponse("TridentWear API running")


@app.get("/products", response_model=None)
@app.get("/api/products", response_model=None)
def list_products(
    request: Request,
    category: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
    format: str | None = Query(default=None),
):
    if request.url.path == "/products" and wants_html(request, format):
        return html_response("shop.html")
    return filter_products(category=category, featured=featured)


@app.get("/products/{product_id}")
@app.get("/api/products/{product_id}")
def read_product(product_id: int) -> dict[str, Any]:
    product = get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product.copy()


@app.post("/products")
@app.post("/api/admin/products")
async def create_product(request: Request) -> dict[str, Any]:
    require_admin(request)
    product_data = await parse_product_submission(request)
    product = normalize_product({"id": next_id(PRODUCTS), **product_data})
    PRODUCTS.append(product)
    return product.copy()


@app.put("/products/{product_id}")
@app.put("/api/admin/products/{product_id}")
async def update_product(product_id: int, request: Request) -> dict[str, Any]:
    require_admin(request)
    existing = get_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    product_data = await parse_product_submission(request, existing=existing)
    updated = normalize_product({"id": product_id, **product_data})
    index = PRODUCTS.index(existing)
    PRODUCTS[index] = updated
    return updated.copy()


@app.delete("/products/{product_id}")
@app.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, request: Request) -> dict[str, Any]:
    require_admin(request)
    existing = get_product_by_id(product_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    PRODUCTS.remove(existing)
    return {"success": True, "message": f'{existing["name"]} deleted.', "deleted_id": product_id}


@app.post("/register")
@app.post("/api/auth/register")
def register(payload: RegisterPayload) -> dict[str, Any]:
    name = str(payload.name or "").strip()
    email = validate_email(payload.email)
    password = str(payload.password or "").strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 2 characters.")
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 6 characters.")
    if find_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")

    user = {
        "id": next_id(USERS),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "customer",
        "created_at": now_iso(),
    }
    USERS.append(user)
    token = create_session(user)
    return {"success": True, "user": serialize_user(user), "token": token}


@app.post("/login")
@app.post("/api/auth/login")
def login(payload: LoginPayload) -> dict[str, Any]:
    email = validate_email(payload.email)
    password = str(payload.password or "").strip()
    user = find_user_by_email(email)

    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    token = create_session(user)
    return {"success": True, "user": serialize_user(user), "token": token}


@app.get("/session")
@app.get("/api/auth/me")
def session_state(request: Request) -> dict[str, Any]:
    user = require_current_user(request)
    return {"authenticated": True, "user": serialize_user(user)}


@app.post("/logout")
@app.post("/api/auth/logout")
def logout(request: Request) -> dict[str, Any]:
    token = get_session_token(request)
    if token:
        SESSIONS.pop(token, None)
    return {"success": True, "message": "Signed out."}


@app.post("/orders")
@app.post("/api/orders")
def create_order(payload: OrderPayload, request: Request) -> dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")

    customer_name = payload.customer.name.strip()
    customer_email = validate_email(payload.customer.email)
    customer_phone = payload.customer.phone.strip()
    shipping_address = payload.shipping.address.strip()
    shipping_city = payload.shipping.city.strip()

    if len(customer_name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer name is required.")
    if len(customer_phone) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A valid phone number is required.")
    if len(shipping_address) < 6 or len(shipping_city) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complete shipping details are required.")

    user = get_current_user(request)
    order = {
        "order_id": f"TRI-{uuid.uuid4().hex[:8].upper()}",
        "items": [item.model_dump() for item in payload.items],
        "subtotal": int(float(payload.subtotal)),
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone,
            "user_id": user["id"] if user else None,
        },
        "shipping": payload.shipping.model_dump(),
        "status": "confirmed",
        "created_at": now_iso(),
    }
    ORDERS.append(order)
    return {"success": True, "message": "Order placed successfully.", "order_id": order["order_id"]}


@app.get("/orders")
@app.get("/api/orders")
def list_orders(request: Request) -> list[dict[str, Any]]:
    require_admin(request)
    return [order.copy() for order in reversed(ORDERS)]


@app.post("/contact")
@app.post("/api/contact")
def create_contact(payload: ContactPayload) -> dict[str, Any]:
    name = str(payload.name or "").strip()
    email = validate_email(payload.email)
    message = str(payload.message or "").strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required.")
    if len(message) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message must be at least 10 characters.")

    CONTACTS.append(
        {
            "id": next_id(CONTACTS),
            "name": name,
            "email": email,
            "message": message,
            "created_at": now_iso(),
        }
    )
    return {"success": True, "message": "Message sent successfully."}


@app.get("/product", include_in_schema=False)
def serve_product_page() -> FileResponse:
    return html_response("product.html")


@app.get("/cart", include_in_schema=False)
def serve_cart_page() -> FileResponse:
    return html_response("cart.html")


@app.get("/auth", include_in_schema=False)
@app.get("/login", include_in_schema=False)
@app.get("/register", include_in_schema=False)
def serve_auth_page() -> FileResponse:
    return html_response("auth.html")


@app.get("/admin", include_in_schema=False)
def serve_admin_page() -> FileResponse:
    return html_response("admin.html")


@app.get("/about", include_in_schema=False)
def serve_about_page() -> FileResponse:
    return html_response("about.html")


@app.get("/privacy", include_in_schema=False)
@app.get("/privacy-policy", include_in_schema=False)
def serve_privacy_page() -> FileResponse:
    return html_response("privacy.html")


@app.get("/terms", include_in_schema=False)
@app.get("/terms-and-conditions", include_in_schema=False)
def serve_terms_page() -> FileResponse:
    return html_response("terms.html")


@app.get("/returns", include_in_schema=False)
@app.get("/return-refund-policy", include_in_schema=False)
def serve_returns_page() -> FileResponse:
    return html_response("returns.html")


@app.get("/shipping", include_in_schema=False)
@app.get("/shipping-policy", include_in_schema=False)
def serve_shipping_page() -> FileResponse:
    return html_response("shipping.html")


@app.get("/contact", include_in_schema=False)
def serve_contact_page() -> FileResponse:
    return html_response("contact.html")


@app.get("/shop", include_in_schema=False)
@app.get("/shop.html", include_in_schema=False)
def legacy_shop_page() -> FileResponse:
    return html_response("shop.html")


@app.get("/index.html", include_in_schema=False)
def legacy_index_page() -> FileResponse:
    return html_response("index.html")


@app.get("/product.html", include_in_schema=False)
def legacy_product_page() -> FileResponse:
    return html_response("product.html")


@app.get("/cart.html", include_in_schema=False)
def legacy_cart_page() -> FileResponse:
    return html_response("cart.html")


@app.get("/auth.html", include_in_schema=False)
def legacy_auth_page() -> FileResponse:
    return html_response("auth.html")


@app.get("/admin.html", include_in_schema=False)
def legacy_admin_page() -> FileResponse:
    return html_response("admin.html")


@app.get("/about.html", include_in_schema=False)
def legacy_about_page() -> FileResponse:
    return html_response("about.html")


@app.get("/privacy.html", include_in_schema=False)
def legacy_privacy_page() -> FileResponse:
    return html_response("privacy.html")


@app.get("/terms.html", include_in_schema=False)
def legacy_terms_page() -> FileResponse:
    return html_response("terms.html")


@app.get("/returns.html", include_in_schema=False)
def legacy_returns_page() -> FileResponse:
    return html_response("returns.html")


@app.get("/shipping.html", include_in_schema=False)
def legacy_shipping_page() -> FileResponse:
    return html_response("shipping.html")


@app.get("/contact.html", include_in_schema=False)
def legacy_contact_page() -> FileResponse:
    return html_response("contact.html")
