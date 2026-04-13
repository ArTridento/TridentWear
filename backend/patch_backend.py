"""
Patch script: adds Inventory, Coupons, Wishlist, Payment (COD + Razorpay stub),
Email notifications, and Wishlist page route to TridentWear backend.
"""
from pathlib import Path

SRC = Path(r"d:\TridentWear\backend\app.py")
text = SRC.read_text(encoding="utf-8")

# ── 1. Path constants ─────────────────────────────────────────
if "COUPONS_PATH" not in text:
    text = text.replace(
        'REVIEWS_PATH = DB_DIR / "reviews.json"',
        'REVIEWS_PATH = DB_DIR / "reviews.json"\n'
        'COUPONS_PATH = DB_DIR / "coupons.json"\n'
        'WISHLIST_PATH = DB_DIR / "wishlist.json"\n'
    )

# ── 2. Pydantic models ────────────────────────────────────────
NEW_MODELS = '''
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

'''
if "class CouponPayload" not in text:
    text = text.replace("class ContactPayload(BaseModel):", NEW_MODELS + "class ContactPayload(BaseModel):")

# ── 3. Data helpers ───────────────────────────────────────────
NEW_HELPERS = '''
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
        f"Hi {order['customer'].get('name', 'Customer')},\\n\\n"
        f"Your TridentWear order {order['order_id']} has been placed!\\n"
        f"Status: {order.get('status','confirmed')}\\n"
        f"Items: {items_text}\\n"
        f"Total: \\u20b9{order.get('subtotal', 0)}\\n\\n"
        f"Thank you for shopping with us!\\n\\nTeam TridentWear"
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

'''
if "def load_coupons()" not in text:
    text = text.replace("def next_id(", NEW_HELPERS + "def next_id(")

# ── 4. ensure_data_files: initialise coupons.json + wishlist.json ─
if 'read_json(COUPONS_PATH' not in text:
    text = text.replace(
        "    contacts = read_json(CONTACTS_PATH, [])\n    write_json(CONTACTS_PATH, contacts)",
        "    contacts = read_json(CONTACTS_PATH, [])\n    write_json(CONTACTS_PATH, contacts)\n"
        "    coupons = read_json(COUPONS_PATH, [])\n    write_json(COUPONS_PATH, coupons)\n"
        "    wishlist = read_json(WISHLIST_PATH, [])\n    write_json(WISHLIST_PATH, wishlist)\n"
    )

# ── 5. Wishlist page route ────────────────────────────────────
if 'serve_wishlist_page' not in text:
    text = text.replace(
        '@pages_router.get("/privacy"',
        '@pages_router.get("/wishlist", include_in_schema=False)\n'
        'def serve_wishlist_page() -> FileResponse:\n'
        '    return html_response("wishlist.html")\n\n\n'
        '@pages_router.get("/privacy"'
    )

# ── 6. New router ──────────────────────────────────────────────
if 'payment_router' not in text:
    text = text.replace(
        'contact_router = APIRouter(prefix="/api", tags=["contact"])',
        'contact_router = APIRouter(prefix="/api", tags=["contact"])\n'
        'payment_router = APIRouter(prefix="/api/payment", tags=["payment"])\n'
        'coupon_router = APIRouter(prefix="/api", tags=["coupons"])\n'
        'wishlist_router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])\n'
    )

# ── 7. Stock check on order creation ──────────────────────────
# Patch create_order to: add coupon support, deduct stock, send email
OLD_ORDER_BODY = 'if not payload.items:\n        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")'
NEW_ORDER_BODY = (
    'if not payload.items:\n        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")\n'
    '    # Stock check\n'
    '    products = load_products()\n'
    '    prod_map = {p["id"]: p for p in products}\n'
    '    for item in payload.items:\n'
    '        pid = int(item.get("id", 0))\n'
    '        qty = max(int(item.get("qty", 1)), 1)\n'
    '        if pid in prod_map and prod_map[pid]["stock"] < qty:\n'
    '            raise HTTPException(status_code=400, detail=f\'Insufficient stock for {prod_map[pid]["name"]}\')\n'
)
if '# Stock check' not in text:
    text = text.replace(OLD_ORDER_BODY, NEW_ORDER_BODY)

# Patch save/return block of create_order to deduct stock + email
OLD_SAVE = "    orders = load_orders()\n    orders.append(order)\n    save_orders(orders)\n    return {\"success\": True, \"message\": \"Order placed successfully.\", \"order_id\": order[\"order_id\"]}"
NEW_SAVE = (
    "    orders = load_orders()\n    orders.append(order)\n    save_orders(orders)\n"
    "    try:\n        deduct_stock(items)\n    except Exception:\n        pass\n"
    "    try:\n        send_order_email(order)\n    except Exception:\n        pass\n"
    "    return {\"success\": True, \"message\": \"Order placed successfully.\", \"order_id\": order[\"order_id\"]}"
)
if "deduct_stock(items)" not in text:
    text = text.replace(OLD_SAVE, NEW_SAVE)

# ── 8. New API endpoints block ────────────────────────────────
NEW_APIS = '''

# ════════════════════════════════════════════════════════════
# COUPON ENDPOINTS
# ════════════════════════════════════════════════════════════
@admin_router.post("/coupons")
def create_coupon(payload: CouponPayload, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    coupons = load_coupons()
    code_upper = payload.code.strip().upper()
    if any(c.get("code", "").upper() == code_upper for c in coupons):
        raise HTTPException(status_code=400, detail="Coupon code already exists.")
    coupon = {
        "id": next_id(coupons),
        "code": code_upper,
        "discount": float(payload.discount),
        "expiry": payload.expiry,
        "usage_limit": max(int(payload.usage_limit), 1),
        "usage_count": 0,
        "created_at": now_iso(),
    }
    coupons.append(coupon)
    save_coupons(coupons)
    return {"success": True, "coupon": coupon}

@admin_router.get("/coupons")
def list_coupons(_: Dict[str, Any] = Depends(require_admin)) -> List[Dict[str, Any]]:
    return load_coupons()

@admin_router.delete("/coupons/{coupon_id}")
def delete_coupon(coupon_id: int, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    coupons = [c for c in load_coupons() if c.get("id") != coupon_id]
    save_coupons(coupons)
    return {"success": True}

@coupon_router.post("/coupons/apply")
def apply_coupon(payload: ApplyCouponPayload) -> Dict[str, Any]:
    result = validate_coupon(payload.code, payload.subtotal)
    return {
        "success": True,
        "code": result["code"],
        "discount_pct": result["discount"],
        "discount_amount": result["discount_amount"],
        "final_total": result["final_total"],
    }


# ════════════════════════════════════════════════════════════
# WISHLIST ENDPOINTS
# ════════════════════════════════════════════════════════════
@wishlist_router.post("/add")
def add_to_wishlist(payload: WishlistPayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    wishlist = load_wishlist()
    entry = {"user_id": user["id"], "product_id": payload.product_id}
    if any(w["user_id"] == user["id"] and w["product_id"] == payload.product_id for w in wishlist):
        return {"success": True, "message": "Already in wishlist."}
    wishlist.append(entry)
    save_wishlist(wishlist)
    return {"success": True, "message": "Added to wishlist."}

@wishlist_router.delete("/remove")
def remove_from_wishlist(payload: WishlistPayload, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    wishlist = [
        w for w in load_wishlist()
        if not (w["user_id"] == user["id"] and w["product_id"] == payload.product_id)
    ]
    save_wishlist(wishlist)
    return {"success": True, "message": "Removed from wishlist."}

@wishlist_router.get("")
def get_wishlist(request: Request) -> List[Dict[str, Any]]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    my_items = [w for w in load_wishlist() if w["user_id"] == user["id"]]
    # Enrich with product info
    products = load_products()
    prod_map = {p["id"]: p for p in products}
    return [
        {**w, "product": prod_map.get(w["product_id"])}
        for w in my_items
        if w["product_id"] in prod_map
    ]


# ════════════════════════════════════════════════════════════
# PAYMENT ENDPOINTS
# ════════════════════════════════════════════════════════════
@payment_router.post("/cod")
def place_cod_order(payload: CODPayload, request: Request) -> Dict[str, Any]:
    """Cash on Delivery – creates order with status 'pending_payment'."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required to place an order.")
    if not payload.items:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    # Stock check
    products = load_products()
    prod_map = {p["id"]: p for p in products}
    for item in payload.items:
        pid = int(item.get("id", 0))
        qty = max(int(item.get("qty", 1)), 1)
        if pid in prod_map and prod_map[pid]["stock"] < qty:
            raise HTTPException(status_code=400, detail=f'Low stock for {prod_map[pid]["name"]}')

    subtotal = float(payload.subtotal)
    discount_amount = 0.0
    coupon_code = None

    if payload.coupon_code:
        try:
            result = validate_coupon(payload.coupon_code, subtotal)
            discount_amount = result["discount_amount"]
            subtotal = result["final_total"]
            coupon_code = result["code"]
            use_coupon(coupon_code)
        except HTTPException as exc:
            raise exc

    items = [
        {
            "id": int(item.get("id", 0)),
            "name": str(item.get("name", "")).strip(),
            "price": int(float(item.get("price", 0) or 0)),
            "image": normalize_image_path(str(item.get("image", ""))),
            "qty": max(int(item.get("qty", 1)), 1),
            "size": str(item.get("size", "")).strip().upper(),
        }
        for item in payload.items
    ]

    order = {
        "order_id": f"TRI-{uuid.uuid4().hex[:8].upper()}",
        "items": items,
        "subtotal": int(subtotal),
        "discount_amount": int(discount_amount),
        "coupon_code": coupon_code,
        "payment_method": "cod",
        "payment_status": "pending",
        "customer": {
            "name": str(payload.customer.get("name", "")).strip(),
            "email": str(payload.customer.get("email", "")).strip(),
            "phone": str(payload.customer.get("phone", "")).strip(),
            "user_id": user["id"],
        },
        "shipping": {
            "address": str(payload.shipping.get("address", "")).strip(),
            "city": str(payload.shipping.get("city", "")).strip(),
            "postal_code": str(payload.shipping.get("postal_code", "")).strip(),
            "country": str(payload.shipping.get("country", "India")).strip() or "India",
            "notes": str(payload.shipping.get("notes", "")).strip(),
        },
        "status": "pending_payment",
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
    return {"success": True, "order_id": order["order_id"], "message": "Order placed (Cash on Delivery)."}


@payment_router.post("/create-order")
def razorpay_create_order(payload: RazorpayCreatePayload, request: Request) -> Dict[str, Any]:
    """Create a Razorpay order. Requires RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET env vars."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        raise HTTPException(status_code=503, detail="Payment gateway not configured. Use COD for now.")
    try:
        import razorpay  # type: ignore
        client = razorpay.Client(auth=(key_id, key_secret))
        rz_order = client.order.create({
            "amount": payload.amount,
            "currency": payload.currency,
            "payment_capture": 1,
        })
        return {"success": True, "razorpay_order_id": rz_order["id"], "key_id": key_id}
    except ImportError:
        raise HTTPException(status_code=503, detail="razorpay package not installed.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@payment_router.post("/verify")
def razorpay_verify(payload: RazorpayVerifyPayload, request: Request) -> Dict[str, Any]:
    """Verify Razorpay payment signature and save the order."""
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Login required.")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_secret:
        raise HTTPException(status_code=503, detail="Payment gateway not configured.")

    # HMAC-SHA256 signature check
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(key_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature.")

    # Build and save order
    od = payload.order_data
    items = od.get("items", [])
    order = {
        "order_id": f"TRI-{uuid.uuid4().hex[:8].upper()}",
        "items": items,
        "subtotal": int(float(od.get("subtotal", 0))),
        "discount_amount": int(float(od.get("discount_amount", 0))),
        "coupon_code": od.get("coupon_code"),
        "payment_method": "razorpay",
        "payment_status": "paid",
        "payment_id": payload.razorpay_payment_id,
        "razorpay_order_id": payload.razorpay_order_id,
        "customer": od.get("customer", {}),
        "shipping": od.get("shipping", {}),
        "status": "confirmed",
        "created_at": now_iso(),
    }
    if od.get("coupon_code"):
        try:
            use_coupon(od["coupon_code"])
        except Exception:
            pass
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
    return {"success": True, "order_id": order["order_id"], "message": "Payment verified, order placed!"}


# ════════════════════════════════════════════════════════════
# ORDER STATUS NOTIFICATION (admin trigger)
# ════════════════════════════════════════════════════════════
@admin_router.post("/orders/{order_id}/notify")
def notify_order_status(order_id: str, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    orders = load_orders()
    order = next((o for o in orders if o.get("order_id") == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    try:
        send_order_email(order)
        return {"success": True, "message": "Notification sent."}
    except Exception as exc:
        return {"success": False, "message": str(exc)}
'''

# Register new routers
INCLUDE_BLOCK = "app.include_router(contact_router)"
NEW_INCLUDES = (
    "app.include_router(contact_router)\n"
    "app.include_router(payment_router)\n"
    "app.include_router(coupon_router)\n"
    "app.include_router(wishlist_router)\n"
)

if "payment_router" not in text:
    if NEW_APIS not in text:
        text += NEW_APIS
    text = text.replace(INCLUDE_BLOCK, NEW_INCLUDES)

SRC.write_text(text, encoding="utf-8")
print("✅ app.py patched successfully.")
