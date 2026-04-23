"""
Production-grade SQLAlchemy models for TridentWear
Uses PostgreSQL with proper relationships and constraints
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, DECIMAL, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PaymentMethod(str, enum.Enum):
    COD = "COD"
    RAZORPAY = "razorpay"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    UPI = "upi"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    # Profile info
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)

    # Verification
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)

    # Addresses
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")

    # Orders
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

    # Wishlist
    wishlist_items = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_email_verified", "email", "is_email_verified"),
    )


class Address(Base):
    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)

    street_address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(10), nullable=False)
    country = Column(String(100), default="India", nullable=False)

    is_default = Column(Boolean, default=False)
    is_billing = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="addresses")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Pricing - DECIMAL for precision
    price = Column(DECIMAL(10, 2), nullable=False)
    cost = Column(DECIMAL(10, 2), nullable=False)
    discount_price = Column(DECIMAL(10, 2), nullable=True)

    # Stock
    stock_quantity = Column(Integer, default=0, nullable=False)

    # Media
    image_url = Column(String(500), nullable=True)
    image_thumbnail_url = Column(String(500), nullable=True)
    gallery_images = Column(JSON, nullable=True)

    # Attributes
    featured = Column(Boolean, default=False, index=True)
    active = Column(Boolean, default=True, index=True)

    # Ratings
    average_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)

    # Relationships
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    wishlist_items = relationship("WishlistItem", back_populates="product", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_category_active", "category", "active"),
        Index("idx_featured", "featured"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Items
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    # Pricing - ALL stored as DECIMAL for accuracy
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    tax_amount = Column(DECIMAL(10, 2), default=0, nullable=False)
    shipping_cost = Column(DECIMAL(10, 2), default=0, nullable=False)
    discount_amount = Column(DECIMAL(10, 2), default=0, nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)

    # Coupon
    coupon_code = Column(String(100), nullable=True)

    # Addresses
    shipping_address = Column(JSON, nullable=False)
    billing_address = Column(JSON, nullable=False)

    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)

    # Payment
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_id = Column(String(255), nullable=True)
    payment_signature = Column(String(255), nullable=True)
    is_payment_verified = Column(Boolean, default=False)

    # Shipping
    tracking_number = Column(String(100), nullable=True)
    shipping_provider = Column(String(100), nullable=True, default="delhivery")

    # Notes
    order_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    paid_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="orders")

    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_status", "status"),
        Index("idx_payment_id", "payment_id"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)

    # Snapshot of product at time of order
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=False)
    product_image = Column(String(500), nullable=True)

    # Pricing snapshot (NEVER use current product price)
    price_at_purchase = Column(DECIMAL(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total = Column(DECIMAL(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    rating = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    review_text = Column(Text, nullable=False)

    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="reviews")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="wishlist_items")
    product = relationship("Product", back_populates="wishlist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="unique_user_product_wishlist"),
    )


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    discount_type = Column(String(50), nullable=False)  # "percent" or "fixed"
    discount_value = Column(DECIMAL(10, 2), nullable=False)
    max_discount_amount = Column(DECIMAL(10, 2), nullable=True)

    min_order_value = Column(DECIMAL(10, 2), default=0)

    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)

    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_till = Column(DateTime(timezone=True), nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_code_active", "code", "is_active"),
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    is_resolved = Column(Boolean, default=False)
    admin_reply = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
