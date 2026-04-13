import re
import os

app_path = r"d:\TridentWear\backend\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add REVIEWS_PATH and functions
if "REVIEWS_PATH =" not in text:
    text = text.replace('CONTACTS_PATH = DB_DIR / "contacts.json"', 'CONTACTS_PATH = DB_DIR / "contacts.json"\nREVIEWS_PATH = DB_DIR / "reviews.json"')

if "def load_reviews()" not in text:
    funcs = """
def load_reviews() -> List[Dict[str, Any]]:
    return read_json(REVIEWS_PATH, [])

def save_reviews(reviews: List[Dict[str, Any]]) -> None:
    write_json(REVIEWS_PATH, reviews)
"""
    text = text.replace('def load_users()', funcs + '\ndef load_users()')

# 2. Add Pydantic Models for Reviews and Order Update
if "class ReviewPayload(BaseModel):" not in text:
    models = """
class ReviewPayload(BaseModel):
    product_id: int
    rating: int
    review: str

class OrderStatusUpdate(BaseModel):
    status: str
"""
    text = text.replace('class ContactPayload(BaseModel):', models + '\nclass ContactPayload(BaseModel):')

# 3. Add Frontend Routes for admin-orders and admin-analytics
routes = """
@pages_router.get("/admin/orders", include_in_schema=False)
def serve_admin_orders() -> FileResponse:
    return html_response("admin-orders.html")

@pages_router.get("/admin/analytics", include_in_schema=False)
def serve_admin_analytics() -> FileResponse:
    return html_response("admin-analytics.html")
"""
if "def serve_admin_orders" not in text:
    text = text.replace('def serve_admin() -> FileResponse:\n    return html_response("admin.html")', 'def serve_admin() -> FileResponse:\n    return html_response("admin.html")' + routes)

# 4. Add Reviews API (POST & GET)
if "def create_review" not in text:
    apis = """
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

@admin_router.get("/orders")
def get_all_orders(_: Dict[str, Any] = Depends(require_admin)) -> List[Dict[str, Any]]:
    return load_orders()

@admin_router.put("/orders/{order_id}")
def update_order_status(order_id: str, payload: OrderStatusUpdate, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    orders = load_orders()
    for o in orders:
        if o.get("order_id") == order_id:
            o["status"] = payload.status
            save_orders(orders)
            return {"success": True, "message": "Order status updated.", "order": o}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

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
"""
    # Just append APIs to the end
    text = text + apis

with open(app_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Updated app.py with all required APIs and routes.")
