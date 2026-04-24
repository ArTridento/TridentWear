from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class OrderItemCreate(BaseModel):
    """Order item creation (product + quantity)"""

    product_id: UUID = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, le=100, description="Quantity 1-100")
    size: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=100)

    @validator("quantity")
    def validate_quantity(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Quantity must be between 1 and 100")
        return v


class OrderCreate(BaseModel):
    """Order creation request"""

    items: list[OrderItemCreate] = Field(..., min_items=1, description="At least 1 item")

    # Shipping address
    shipping_name: str = Field(..., min_length=2, max_length=255)
    shipping_email: EmailStr
    shipping_phone: str = Field(..., max_length=20)
    shipping_address: str = Field(..., min_length=5, max_length=500)
    shipping_city: str = Field(..., max_length=100)
    shipping_state: str = Field(..., max_length=100)
    shipping_postal_code: str = Field(..., max_length=20)
    shipping_country: str = Field("India", max_length=100)

    notes: Optional[str] = Field(None, max_length=500)

    @validator("shipping_postal_code")
    def validate_postal_code(cls, v):
        """Validate postal code format (6 digits for India)"""
        if not v.replace("-", "").replace(" ", "").isdigit():
            raise ValueError("Postal code must be numeric")
        return v


class OrderItemResponse(BaseModel):
    """Order item response"""

    id: UUID
    product_id: UUID
    product_name: str
    product_sku: str
    quantity: int
    price_per_unit: Decimal
    discount_percent: Decimal
    total: Decimal
    size: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response schema"""

    id: UUID
    user_id: UUID
    items: list[OrderItemResponse]

    # Pricing
    subtotal: Decimal
    tax: Decimal
    shipping_cost: Decimal
    discount: Decimal
    total: Decimal

    # Payment info
    payment_method: str
    payment_status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None

    # Shipping info
    shipping_name: str
    shipping_email: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_state: str
    shipping_postal_code: str
    shipping_country: str

    # Status
    status: str
    notes: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentVerifyRequest(BaseModel):
    """Payment verification request from Razorpay"""

    razorpay_order_id: str = Field(..., description="Razorpay Order ID")
    razorpay_payment_id: str = Field(..., description="Razorpay Payment ID")
    razorpay_signature: str = Field(..., description="Razorpay Signature")

    @validator("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class RazorpayOrderResponse(BaseModel):
    """Razorpay order creation response"""

    order_id: UUID  # Our database order ID
    razorpay_order_id: str  # Razorpay Order ID
    amount: int  # Amount in paisa (₹100 = 10000 paisa)
    currency: str = "INR"


class OrderListResponse(BaseModel):
    """Paginated order list response"""

    total: int
    page: int
    per_page: int
    items: list[OrderResponse]
