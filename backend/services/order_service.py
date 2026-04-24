from sqlalchemy.orm import Session
from models.product import Product
from models.order import Order, OrderItem, OrderStatus, PaymentStatus
from schemas.order import OrderCreate, OrderItemCreate
from uuid import UUID
from decimal import Decimal
from typing import Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ========== PRICING CONSTANTS ==========
TAX_RATE = Decimal("0.18")  # 18% GST for India
SHIPPING_COST_THRESHOLD = Decimal("500")  # Free shipping above ₹500
BASE_SHIPPING_COST = Decimal("50")  # ₹50 shipping


class OrderService:
    """Order processing with price protection"""

    @staticmethod
    def validate_order_items(items: List[OrderItemCreate], db: Session) -> List[Dict[str, Any]]:
        """
        Validate order items and fetch current prices from database.

        CRITICAL: Never trust frontend prices. Always fetch from backend.

        Args:
            items: Order items from frontend
            db: Database session

        Returns:
            List of validated items with database prices
        """
        validated_items = []

        for item in items:
            # ========== FETCH PRODUCT FROM DATABASE ==========
            product = db.query(Product).filter(Product.id == item.product_id).first()

            if not product:
                raise ValueError(f"Product not found: {item.product_id}")

            if not product.is_active:
                raise ValueError(f"Product is not available: {product.name}")

            # ========== VALIDATE STOCK ==========
            if not product.can_order(item.quantity):
                raise ValueError(
                    f"Insufficient stock for {product.name}. Available: {product.stock}"
                )

            # ========== CALCULATE PRICE (BACKEND ONLY) ==========
            # Get current price from database, not frontend
            unit_price = product.get_discounted_price()
            line_total = Decimal(str(unit_price)) * Decimal(str(item.quantity))

            validated_items.append(
                {
                    "product": product,
                    "quantity": item.quantity,
                    "size": item.size,
                    "color": item.color,
                    "unit_price": Decimal(str(unit_price)),
                    "discount_percent": product.discount_percent,
                    "line_total": line_total,
                }
            )

        if not validated_items:
            raise ValueError("Order must contain at least one item")

        return validated_items

    @staticmethod
    def calculate_order_totals(validated_items: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """
        Calculate order totals including tax and shipping.

        Args:
            validated_items: List of validated order items

        Returns:
            Dictionary with subtotal, tax, shipping, discount, total
        """
        # ========== CALCULATE SUBTOTAL ==========
        subtotal = sum(item["line_total"] for item in validated_items)

        # ========== CALCULATE TAX (18% GST) ==========
        tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))

        # ========== CALCULATE SHIPPING ==========
        # Free shipping for orders above ₹500
        if subtotal >= SHIPPING_COST_THRESHOLD:
            shipping_cost = Decimal("0.00")
        else:
            shipping_cost = BASE_SHIPPING_COST

        # ========== CALCULATE TOTAL ==========
        total = (subtotal + tax + shipping_cost).quantize(Decimal("0.01"))

        return {
            "subtotal": subtotal,
            "tax": tax,
            "shipping_cost": shipping_cost,
            "discount": Decimal("0.00"),  # For future coupon implementation
            "total": total,
        }

    @staticmethod
    def create_order(
        user_id: UUID,
        order_data: OrderCreate,
        validated_items: List[Dict[str, Any]],
        totals: Dict[str, Decimal],
        db: Session,
    ) -> Order:
        """
        Create an order with all validated data.

        Args:
            user_id: User UUID
            order_data: Order request data
            validated_items: Validated items with prices
            totals: Calculated totals
            db: Database session

        Returns:
            Created Order object
        """
        # ========== CREATE ORDER ==========
        order = Order(
            user_id=user_id,
            subtotal=totals["subtotal"],
            tax=totals["tax"],
            shipping_cost=totals["shipping_cost"],
            discount=totals["discount"],
            total=totals["total"],
            payment_status=PaymentStatus.PENDING,
            status=OrderStatus.PENDING,
            shipping_name=order_data.shipping_name,
            shipping_email=order_data.shipping_email,
            shipping_phone=order_data.shipping_phone,
            shipping_address=order_data.shipping_address,
            shipping_city=order_data.shipping_city,
            shipping_state=order_data.shipping_state,
            shipping_postal_code=order_data.shipping_postal_code,
            shipping_country=order_data.shipping_country,
            notes=order_data.notes,
        )

        db.add(order)
        db.flush()  # Get order ID without committing

        # ========== CREATE ORDER ITEMS ==========
        for item in validated_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item["product"].id,
                product_name=item["product"].name,
                product_sku=item["product"].sku,
                quantity=item["quantity"],
                price_per_unit=item["unit_price"],
                discount_percent=item["discount_percent"],
                total=item["line_total"],
                size=item.get("size"),
                color=item.get("color"),
            )
            order.items.append(order_item)

        # ========== RESERVE STOCK (OPTIONAL: Implement later for strict inventory) ==========
        # For now, we don't reduce stock until payment is confirmed
        # This prevents issues with failed payments

        db.commit()
        db.refresh(order)

        logger.info(f"Order created: {order.id} for user {user_id}")

        return order

    @staticmethod
    def get_order_by_id(order_id: UUID, db: Session) -> Order:
        """
        Get order by ID.

        Args:
            order_id: Order UUID
            db: Database session

        Returns:
            Order object
        """
        order = db.query(Order).filter(Order.id == order_id).first()

        if not order:
            raise ValueError(f"Order not found: {order_id}")

        return order

    @staticmethod
    def reduce_product_stock(order: Order, db: Session) -> None:
        """
        Reduce product stock after payment confirmation.

        Args:
            order: Completed order
            db: Database session
        """
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()

            if product:
                product.stock -= item.quantity
                logger.info(
                    f"Stock reduced for product {product.sku}: {item.quantity} units"
                )

        db.commit()

    @staticmethod
    def get_user_orders(user_id: UUID, db: Session, skip: int = 0, limit: int = 10) -> tuple[list[Order], int]:
        """
        Get all orders for a user with pagination.

        Args:
            user_id: User UUID
            db: Database session
            skip: Number of records to skip
            limit: Number of records to return

        Returns:
            Tuple of (orders list, total count)
        """
        query = db.query(Order).filter(Order.user_id == user_id)
        total = query.count()

        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

        return orders, total

    @staticmethod
    def cancel_order(order_id: UUID, db: Session) -> Order:
        """
        Cancel an order (only if payment not completed).

        Args:
            order_id: Order UUID
            db: Database session

        Returns:
            Cancelled order
        """
        order = OrderService.get_order_by_id(order_id, db)

        if order.payment_status == PaymentStatus.COMPLETED:
            raise ValueError("Cannot cancel a paid order")

        order.status = OrderStatus.CANCELLED
        db.commit()
        db.refresh(order)

        logger.info(f"Order cancelled: {order_id}")

        return order
