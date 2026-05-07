from fastapi import APIRouter
from typing import Dict, Any, Optional

from app.services.product_service import get_all_products, get_single_product

router = APIRouter(prefix="/api/v1/products", tags=["products"])

@router.get("")
def get_products(category: Optional[str] = None, featured: Optional[bool] = None) -> Dict[str, Any]:
    return get_all_products(category, featured)

@router.get("/{product_id}")
def get_product(product_id: int) -> Dict[str, Any]:
    return get_single_product(product_id)
