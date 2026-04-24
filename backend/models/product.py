import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Product(Base):
    """
    Product model for inventory management.
    Prices stored as Decimal for accuracy (never float).
    Stock validation happens on backend.
    """

    __tablename__ = "products"

    # ========== PRIMARY KEY ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    # ========== PRODUCT DETAILS ==========
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)

    # ========== PRICING (CRITICAL FOR SECURITY) ==========
    # Using Numeric for precision (never float for money)
    price = Column(Numeric(10, 2), nullable=False)  # ₹ 9999.99 max
    cost = Column(Numeric(10, 2), nullable=False)  # Internal cost tracking
    discount_percent = Column(Numeric(5, 2), default=0, nullable=False)  # 0-100%

    # ========== INVENTORY MANAGEMENT ==========
    stock = Column(Integer, default=0, nullable=False)  # Current stock quantity
    min_stock = Column(Integer, default=10, nullable=False)  # Reorder level

    # ========== PRODUCT METADATA ==========
    category = Column(String(100), nullable=True, index=True)
    size = Column(String(50), nullable=True)  # XS, S, M, L, XL, XXL
    color = Column(String(100), nullable=True)
    material = Column(String(255), nullable=True)
    image_url = Column(String(500), nullable=True)
    image_alt_text = Column(String(255), nullable=True)

    # ========== STATUS ==========
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False)

    # ========== TIMESTAMPS ==========
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ========== RATINGS (OPTIONAL) ==========
    average_rating = Column(Numeric(3, 2), default=0, nullable=False)  # 0.00 - 5.00
    total_reviews = Column(Integer, default=0, nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"

    def get_discounted_price(self):
        """Calculate discounted price"""
        if self.discount_percent:
            discount_amount = float(self.price) * float(self.discount_percent) / 100
            return float(self.price) - discount_amount
        return float(self.price)

    def can_order(self, quantity: int) -> bool:
        """Check if product can be ordered with given quantity"""
        return self.is_active and self.stock >= quantity
