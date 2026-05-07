import os
import json
import uuid
import smtplib
import ssl
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from fastapi import HTTPException, status, Request

from app.services.product_service import load_products, deduct_stock, normalize_image_path
from app.services.auth_service import get_session_user, validate_email

from app.db.json_manager import read_json, update_json

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = BASE_DIR / "db"
ORDERS_PATH = str(DB_DIR / "orders.json")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_orders() -> List[Dict[str, Any]]:
    return read_json(ORDERS_PATH) or []

def send_order_email(order: Dict[str, Any]) -> None:
    """Non-blocking email; silently skips if SMTP not configured."""
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
    msg["Subject"] = f"Order Confirmed - {order['order_id']}"
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
        pass

def get_stats_data() -> Dict[str, int]:
    orders = load_orders()
    unique_users = set(o.get("customer", {}).get("email") for o in orders if o.get("customer", {}).get("email"))
    baseline = 150
    return {"customers": baseline + len(unique_users) if unique_users else baseline + len(orders)}

def process_create_order(payload: Any, request: Request) -> Dict[str, Any]:
    if not payload.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")
    
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
    
    subtotal = sum(i["price"] * i["qty"] for i in items)
    session_user = get_session_user(request)
    
    new_order = None
    def _create_order(orders: list):
        nonlocal new_order
        if not orders:
            orders = []
        
        order_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
        new_order = {
            "id": next_id(orders),
            "order_id": order_id,
            "customer": {
                "user_id": session_user["id"] if session_user else None,
                "name": customer_name,
                "email": customer_email,
                "phone": shipping_phone
            },
            "shipping": {
                "address": shipping_address,
                "city": shipping_city,
                "pincode": str(payload.shipping.get("pincode", "")).strip()
            },
            "items": payload.items,
            "subtotal": subtotal,
            "payment_method": payload.payment_method,
            "status": "confirmed",
            "created_at": now_iso()
        }
        orders.append(new_order)
        return orders

    update_json(ORDERS_PATH, _create_order)
    
    # After order is successfully written, deduct stock
    deduct_stock(payload.items)

    try:
        send_order_email(new_order)
    except Exception:
        pass
        
    return {"success": True, "message": "Order placed successfully.", "order_id": new_order["order_id"]}

def get_user_orders_data(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in to view orders.")
    orders = load_orders()
    user_orders = [o for o in orders if o.get("customer", {}).get("user_id") == user["id"]]
    user_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return {"success": True, "orders": user_orders}

def cancel_order_logic(order_id: str, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in.")
    
    cancelled = False
    def _cancel(orders: list):
        nonlocal cancelled
        for o in orders:
            if o.get("order_id") == order_id and o.get("customer", {}).get("user_id") == user["id"]:
                if o.get("status") in ("shipped", "delivered"):
                    raise HTTPException(status_code=400, detail="Cannot cancel a shipped order.")
                o["status"] = "cancelled"
                cancelled = True
                break
        return orders

    update_json(ORDERS_PATH, _cancel)
    if cancelled:
        return {"success": True, "message": "Order cancelled."}
    raise HTTPException(status_code=404, detail="Order not found.")

def track_order_logic(order_id: str) -> Dict[str, Any]:
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

def create_shiprocket_shipment(order: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "shipped",
        "tracking_id": f"SR{uuid.uuid4().hex[:8].upper()}",
        "courier": "Delhivery (Shiprocket)",
        "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=4)).date().isoformat()
    }

def get_all_orders_data() -> List[Dict[str, Any]]:
    return load_orders()

def update_order_status_logic(order_id: str, payload_status: str) -> Dict[str, Any]:
    updated_order = None
    def _update_status(orders: list):
        nonlocal updated_order
        for o in orders:
            if o.get("order_id") == order_id:
                o["status"] = payload_status
                if payload_status == "shipped" and not o.get("tracking_id"):
                    try:
                        shipment = create_shiprocket_shipment(o)
                        o["tracking_id"] = shipment["tracking_id"]
                        o["courier"] = shipment["courier"]
                        o["estimated_delivery"] = shipment["estimated_delivery"]
                    except Exception:
                        pass
                updated_order = o
                break
        return orders

    update_json(ORDERS_PATH, _update_status)
    if updated_order:
        return {"success": True, "message": "Order status updated.", "order": updated_order}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

def next_id(items: List[Dict[str, Any]]) -> int:
    if not items:
        return 1
    return max(int(item.get("id", 0)) for item in items) + 1

def create_payment_order_record(order_data: Dict[str, Any]) -> Dict[str, Any]:
    new_order = None
    def _create_record(orders: list):
        nonlocal new_order
        if not orders:
            orders = []
        order_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"
        
        new_order = {
            "id": next_id(orders),
            "order_id": order_id,
            "created_at": now_iso(),
            **order_data
        }
        orders.append(new_order)
        return orders

    update_json(ORDERS_PATH, _create_record)
    
    try:
        send_order_email(new_order)
    except Exception:
        pass
        
    return new_order
