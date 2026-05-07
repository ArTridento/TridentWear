from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Dict, Any, List

from app.services.order_service import (
    get_stats_data,
    process_create_order,
    get_user_orders_data,
    cancel_order_logic,
    track_order_logic
)

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

class OrderPayload(BaseModel):
    items: List[Dict[str, Any]]
    subtotal: float
    customer: Dict[str, Any]
    shipping: Dict[str, Any]

@router.get("/stats")
def get_stats() -> Dict[str, int]:
    return get_stats_data()

@router.post("")
def create_order(payload: OrderPayload, request: Request) -> Dict[str, Any]:
    return process_create_order(payload, request)

@router.get("")
def get_user_orders(request: Request) -> Dict[str, Any]:
    return get_user_orders_data(request)

@router.put("/{order_id}/cancel")
def cancel_order(order_id: str, request: Request) -> Dict[str, Any]:
    return cancel_order_logic(order_id, request)

@router.get("/{order_id}/tracking")
def track_order(order_id: str) -> Dict[str, Any]:
    return track_order_logic(order_id)
