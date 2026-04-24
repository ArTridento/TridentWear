import razorpay
import hmac
import hashlib
from sqlalchemy.orm import Session
from models.order import Order, OrderStatus, PaymentStatus
from config import get_settings
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

settings = get_settings()

# ========== RAZORPAY CLIENT ==========
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class PaymentService:
    """Razorpay payment processing"""

    @staticmethod
    def create_razorpay_order(order: Order, db: Session) -> Dict[str, Any]:
        """
        Create a Razorpay order for payment.

        Args:
            order: Order object from database
            db: Database session

        Returns:
            Razorpay order details
        """
        try:
            # ========== CONVERT TO PAISA (₹100 = 10000 paisa) ==========
            amount_in_paisa = int(float(order.total) * 100)

            # ========== CREATE RAZORPAY ORDER ==========
            razorpay_order = razorpay_client.order.create(
                {
                    "amount": amount_in_paisa,
                    "currency": "INR",
                    "receipt": str(order.id),
                    "notes": {
                        "order_id": str(order.id),
                        "customer_email": order.shipping_email,
                    },
                }
            )

            # ========== SAVE RAZORPAY ORDER ID ==========
            order.razorpay_order_id = razorpay_order["id"]
            db.commit()

            logger.info(f"Razorpay order created: {razorpay_order['id']} for order {order.id}")

            return {
                "order_id": str(order.id),
                "razorpay_order_id": razorpay_order["id"],
                "amount": amount_in_paisa,
                "currency": "INR",
            }

        except Exception as e:
            logger.error(f"Error creating Razorpay order: {str(e)}")
            raise ValueError(f"Failed to create payment order: {str(e)}")

    @staticmethod
    def verify_payment(
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verify Razorpay payment using HMAC SHA256 signature.

        CRITICAL: This prevents payment tampering and fraud.

        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay

        Returns:
            True if signature is valid (payment is legitimate)
        """
        try:
            # ========== CREATE SIGNATURE ==========
            # Format: "{order_id}|{payment_id}"
            data = f"{razorpay_order_id}|{razorpay_payment_id}"

            # ========== COMPUTE HMAC SHA256 ==========
            computed_signature = hmac.new(
                key=settings.RAZORPAY_KEY_SECRET.encode(),
                msg=data.encode(),
                digestmod=hashlib.sha256,
            ).hexdigest()

            # ========== COMPARE SIGNATURES ==========
            # Use timing-safe comparison to prevent timing attacks
            is_valid = hmac.compare_digest(computed_signature, razorpay_signature)

            if is_valid:
                logger.info(f"Payment verified successfully: {razorpay_payment_id}")
            else:
                logger.warning(f"Payment verification failed: {razorpay_payment_id}")
                logger.warning(f"Expected: {computed_signature}, Got: {razorpay_signature}")

            return is_valid

        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False

    @staticmethod
    def mark_payment_completed(order: Order, razorpay_payment_id: str, db: Session) -> Order:
        """
        Mark order payment as completed.

        Args:
            order: Order object
            razorpay_payment_id: Razorpay Payment ID
            db: Database session

        Returns:
            Updated order
        """
        order.payment_status = PaymentStatus.COMPLETED
        order.razorpay_payment_id = razorpay_payment_id
        order.status = OrderStatus.PROCESSING
        order.paid_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        logger.info(f"Payment marked completed for order: {order.id}")

        return order

    @staticmethod
    def mark_payment_failed(order: Order, db: Session) -> Order:
        """
        Mark order payment as failed.

        Args:
            order: Order object
            db: Database session

        Returns:
            Updated order
        """
        order.payment_status = PaymentStatus.FAILED
        order.status = OrderStatus.FAILED

        db.commit()
        db.refresh(order)

        logger.info(f"Payment marked failed for order: {order.id}")

        return order

    @staticmethod
    def get_razorpay_webhook_key() -> str:
        """
        Get webhook key for validating Razorpay webhooks.

        Returns:
            Webhook secret key
        """
        return settings.RAZORPAY_WEBHOOK_SECRET

    @staticmethod
    def verify_webhook_signature(
        webhook_body: str, webhook_signature: str
    ) -> bool:
        """
        Verify Razorpay webhook signature.

        Args:
            webhook_body: Raw webhook body (JSON string)
            webhook_signature: Signature header from webhook

        Returns:
            True if signature is valid
        """
        try:
            computed_signature = hmac.new(
                key=settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                msg=webhook_body.encode(),
                digestmod=hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(computed_signature, webhook_signature)

        except Exception as e:
            logger.error(f"Webhook verification error: {str(e)}")
            return False
