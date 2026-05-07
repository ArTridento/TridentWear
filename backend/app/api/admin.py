from fastapi import APIRouter, Depends, Request, Form, File, UploadFile
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.auth_service import require_admin
from app.services.product_service import process_create_product, process_update_product, process_delete_product
from app.services.order_service import get_all_orders_data, update_order_status_logic
from app.services.admin_service import get_analytics_data

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

class OrderStatusUpdate(BaseModel):
    status: str

@router.post("/products")
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
    return await process_create_product(name, category, price, description, tag, sizes, stock, featured, image)

@router.put("/products/{product_id}")
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
    return await process_update_product(product_id, name, category, price, description, tag, sizes, stock, featured, image)

@router.delete("/products/{product_id}")
def delete_product(product_id: int, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    return process_delete_product(product_id)

@router.get("/orders")
def get_all_orders(_: Dict[str, Any] = Depends(require_admin)) -> List[Dict[str, Any]]:
    return get_all_orders_data()

@router.put("/orders/{order_id}")
def update_order_status(order_id: str, payload: OrderStatusUpdate, _: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    return update_order_status_logic(order_id, payload.status)

@router.get("/analytics")
def get_analytics(_: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    return get_analytics_data()
