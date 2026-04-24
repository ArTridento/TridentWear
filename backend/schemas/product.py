from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ProductCreate(BaseModel):
    """Product creation schema (admin only)"""

    name: str = Field(..., min_length=3, max_length=255, description="Product name")
    description: Optional[str] = Field(None, max_length=2000)
    sku: str = Field(..., min_length=3, max_length=100, description="SKU must be unique")
    price: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Price > 0")
    cost: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2, description="Cost > 0")
    discount_percent: Decimal = Field(0, ge=0, le=100, description="0-100%")
    stock: int = Field(0, ge=0, description="Stock quantity >= 0")
    min_stock: int = Field(10, ge=1, description="Minimum stock level")
    category: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)  # XS, S, M, L, XL, XXL
    color: Optional[str] = Field(None, max_length=100)
    material: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(True, description="Is product active?")
    is_featured: bool = Field(False, description="Is product featured?")

    @validator("price", "cost")
    def validate_price(cls, v):
        """Ensure price is positive and reasonable"""
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        if v > 9999.99:
            raise ValueError("Price exceeds maximum limit")
        return v

    @validator("discount_percent")
    def validate_discount(cls, v):
        """Ensure discount is between 0-100"""
        if not (0 <= v <= 100):
            raise ValueError("Discount must be between 0-100%")
        return v


class ProductUpdate(BaseModel):
    """Product update schema (admin only)"""

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    cost: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=2)
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=1)
    category: Optional[str] = Field(None, max_length=100)
    size: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=100)
    material: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

    @validator("price", "cost", pre=True, always=True)
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class ProductResponse(BaseModel):
    """Product response schema"""

    id: UUID
    name: str
    description: Optional[str] = None
    sku: str
    price: Decimal
    cost: Optional[Decimal] = None  # Don't expose cost to customers
    discount_percent: Decimal
    discounted_price: Optional[float] = None  # Calculated price
    stock: int
    category: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    is_featured: bool
    average_rating: Decimal
    total_reviews: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated product list response"""

    total: int
    page: int
    per_page: int
    items: list[ProductResponse]
