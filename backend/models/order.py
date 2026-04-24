import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import enum


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "PENDING"  # Order created, awaiting payment
    PROCESSING = "PROCESSING"  # Payment verified, preparing shipment
    SHIPPED = "SHIPPED"  # Order shipped
    DELIVERED = "DELIVERED"  # Order delivered
    CANCELLED = "CANCELLED"  # Order cancelled
    FAILED = "FAILED"  # Payment failed


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Order(Base):
    """
    Order model - stores complete order snapshot.
    CRITICAL: Prices are locked at order time to prevent tampering.
    """

    __tablename__ = "orders"

    # ========== PRIMARY KEY ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========== CUSTOMER INFO ==========
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ========== ORDER PRICING (LOCKED AT ORDER TIME) ==========
    subtotal = Column(Numeric(10, 2), nullable=False)  # Sum of line items
    tax = Column(Numeric(10, 2), default=0, nullable=False)  # Tax amount
    shipping_cost = Column(Numeric(10, 2), default=0, nullable=False)  # Shipping charges
    discount = Column(Numeric(10, 2), default=0, nullable=False)  # Applied discount
    total = Column(Numeric(10, 2), nullable=False)  # Final amount to pay

    # ========== PAYMENT INFO ==========
    payment_method = Column(String(50), default="RAZORPAY", nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    razorpay_order_id = Column(String(100), nullable=True, index=True)  # Razorpay order ID
    razorpay_payment_id = Column(String(100), nullable=True, index=True)  # Razorpay payment ID
    razorpay_signature = Column(String(255), nullable=True)  # Signature for verification

    # ========== SHIPPING ADDRESS (SNAPSHOT) ==========
    shipping_name = Column(String(255), nullable=False)
    shipping_email = Column(String(255), nullable=False)
    shipping_phone = Column(String(20), nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_city = Column(String(100), nullable=False)
    shipping_state = Column(String(100), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_country = Column(String(100), default="India", nullable=False)

    # ========== ORDER STATUS ==========
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)

    # ========== ORDER NOTES ==========
    notes = Column(Text, nullable=True)

    # ========== TIMESTAMPS ==========
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    # ========== RELATIONSHIPS ==========
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total={self.total}, status={self.status})>"


class OrderItem(Base):
    """
    Order item model - individual line items in an order.
    CRITICAL: Price per unit is locked at order creation.
    """

    __tablename__ = "order_items"

    # ========== PRIMARY KEY ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========== RELATIONSHIPS ==========
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)

    # ========== ITEM DETAILS ==========
    product_name = Column(String(255), nullable=False)  # Snapshot of product name
    product_sku = Column(String(100), nullable=False)  # Snapshot of SKU
    quantity = Column(Integer, nullable=False)

    # ========== PRICING (LOCKED AT ORDER TIME) ==========
    price_per_unit = Column(Numeric(10, 2), nullable=False)  # Price at order time
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)  # Discount applied
    total = Column(Numeric(10, 2), nullable=False)  # quantity * price_per_unit

    # ========== PRODUCT ATTRIBUTES ==========
    size = Column(String(50), nullable=True)
    color = Column(String(100), nullable=True)

    # ========== TIMESTAMPS ==========
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ========== RELATIONSHIPS ==========
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity}, total={self.total})>"
