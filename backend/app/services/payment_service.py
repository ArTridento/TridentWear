import os
import uuid
from typing import Dict, Any
from fastapi import Request
from app.services.order_service import create_payment_order_record
from app.services.auth_service import get_session_user

def process_cod_order(
    subtotal: float,
    customer: Dict[str, Any],
    shipping: Dict[str, Any],
    items: list,
    coupon_code: str = None,
    test_mode: bool = False,
    request: Request = None,
) -> Dict[str, Any]:
    # Inject logged-in user_id so orders appear in profile history
    if request is not None:
        session_user = get_session_user(request)
        if session_user:
            customer = {**customer, "user_id": session_user["id"]}
    order_data = {
        "method": "COD",
        "payment_method": "cod",
        "payment_status": "cod_pending",
        "subtotal": subtotal,
        "total": subtotal,
        "customer": customer,
        "shipping": shipping,
        "items": items,
        "coupon_code": coupon_code,
        "status": "placed",
        "test_mode": test_mode,
    }
    
    new_order = create_payment_order_record(order_data)
    return {"success": True, "order_id": new_order["order_id"], "message": "COD order placed successfully"}

def process_razorpay_create(amount: int, currency: str = "INR") -> Dict[str, Any]:
    rz_key = os.getenv("RAZORPAY_KEY", "rzp_test_mockkey")
    mock_order_id = f"order_{uuid.uuid4().hex[:14]}"
    return {
        "success": True,
        "razorpay_order_id": mock_order_id,
        "key_id": rz_key
    }

def process_razorpay_verify(razorpay_payment_id: str, order_data_payload: Dict[str, Any], request: Request = None) -> Dict[str, Any]:
    test_mode = bool(order_data_payload.get("test_mode", False))
    customer = dict(order_data_payload.get("customer") or {})
    # Inject logged-in user_id
    if request is not None:
        session_user = get_session_user(request)
        if session_user:
            customer["user_id"] = session_user["id"]
    order_data = {
        "method": "Razorpay",
        "payment_method": "razorpay",
        "razorpay_payment_id": razorpay_payment_id,
        "subtotal": order_data_payload.get("subtotal"),
        "total": order_data_payload.get("subtotal"),
        "discount_amount": order_data_payload.get("discount_amount", 0),
        "customer": customer,
        "shipping": order_data_payload.get("shipping"),
        "items": order_data_payload.get("items"),
        "coupon_code": order_data_payload.get("coupon_code"),
        "status": "placed",
        "payment_status": "paid",
        "test_mode": test_mode,
    }
    
    new_order = create_payment_order_record(order_data)
    return {"success": True, "order_id": new_order["order_id"], "message": "Payment verified and order placed"}
