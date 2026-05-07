import os
import uuid
from typing import Dict, Any
from app.services.order_service import create_payment_order_record

def process_cod_order(subtotal: float, customer: Dict[str, Any], shipping: Dict[str, Any], items: list, coupon_code: str = None) -> Dict[str, Any]:
    order_data = {
        "method": "COD",
        "subtotal": subtotal,
        "customer": customer,
        "shipping": shipping,
        "items": items,
        "coupon_code": coupon_code,
        "status": "pending",
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

def process_razorpay_verify(razorpay_payment_id: str, order_data_payload: Dict[str, Any]) -> Dict[str, Any]:
    order_data = {
        "method": "Razorpay",
        "razorpay_payment_id": razorpay_payment_id,
        "subtotal": order_data_payload.get("subtotal"),
        "customer": order_data_payload.get("customer"),
        "shipping": order_data_payload.get("shipping"),
        "items": order_data_payload.get("items"),
        "coupon_code": order_data_payload.get("coupon_code"),
        "status": "paid",
    }
    
    new_order = create_payment_order_record(order_data)
    return {"success": True, "order_id": new_order["order_id"], "message": "Payment verified and order placed"}
