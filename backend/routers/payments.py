from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.order import Order
from schemas.order import PaymentVerifyRequest, RazorpayOrderResponse
from services.payment_service import PaymentService
from services.order_service import OrderService
from services.email_service import EmailService
from middleware.rate_limit import limiter, RATE_LIMIT_NORMAL
from routers.auth import get_current_user
from typing import Optional
from uuid import UUID
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# ========== CREATE RAZORPAY ORDER ==========
@router.post("/create-order", response_model=RazorpayOrderResponse)
@limiter.limit(RATE_LIMIT_NORMAL)
async def create_razorpay_order(
    request,  # For rate limiter
    order_id: UUID = Body(..., embed=True, description="Order ID from /orders POST response"),
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create a Razorpay order for payment.

    Call this after creating an order via /api/orders

    Args:
        order_id: Order UUID from order creation response
        authorization: JWT token

    Returns:
        Razorpay order details
    """
    try:
        # ========== AUTHENTICATE USER ==========
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        token = authorization.replace("Bearer ", "")
        user = await get_current_user(token, db)

        # ========== FETCH ORDER ==========
        order = OrderService.get_order_by_id(order_id, db)

        # ========== VERIFY OWNERSHIP ==========
        if order.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only pay for your own orders",
            )

        # ========== CREATE RAZORPAY ORDER ==========
        razorpay_order = PaymentService.create_razorpay_order(order, db)

        logger.info(f"Razorpay order created: {razorpay_order['razorpay_order_id']}")

        return razorpay_order

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Razorpay order creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment order",
        )


# ========== VERIFY PAYMENT ==========
@router.post("/verify", status_code=status.HTTP_200_OK)
@limiter.limit(RATE_LIMIT_NORMAL)
async def verify_payment(
    request,  # For rate limiter
    payment_data: PaymentVerifyRequest,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Verify Razorpay payment signature.

    CRITICAL: This prevents payment tampering.

    Args:
        payment_data: Razorpay payment details
        authorization: JWT token

    Returns:
        Payment status
    """
    try:
        # ========== AUTHENTICATE USER ==========
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        token = authorization.replace("Bearer ", "")
        user = await get_current_user(token, db)

        # ========== FETCH ORDER ==========
        # Get order by razorpay_order_id
        order = db.query(Order).filter(
            Order.razorpay_order_id == payment_data.razorpay_order_id
        ).first()

        if not order:
            logger.warning(f"Order not found for Razorpay order: {payment_data.razorpay_order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # ========== VERIFY OWNERSHIP ==========
        if order.user_id != user.id:
            logger.warning(f"Unauthorized payment verification attempt for order {order.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only verify your own orders",
            )

        # ========== VERIFY PAYMENT SIGNATURE ==========
        # This is the CRITICAL security check
        is_valid = PaymentService.verify_payment(
            payment_data.razorpay_order_id,
            payment_data.razorpay_payment_id,
            payment_data.razorpay_signature,
        )

        if not is_valid:
            logger.warning(
                f"Payment verification failed for order {order.id}: "
                f"Invalid signature"
            )
            # Mark as failed
            PaymentService.mark_payment_failed(order, db)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment verification failed",
            )

        # ========== PAYMENT IS VALID - UPDATE ORDER ==========
        order = PaymentService.mark_payment_completed(
            order, payment_data.razorpay_payment_id, db
        )

        # ========== REDUCE PRODUCT STOCK ==========
        OrderService.reduce_product_stock(order, db)

        # ========== SEND CONFIRMATION EMAIL ==========
        # Build email data
        items = []
        for item in order.items:
            items.append({
                "name": item.product_name,
                "quantity": item.quantity,
                "unit_price": float(item.price_per_unit),
                "total": float(item.total),
            })

        EmailService.send_order_confirmation_email(
            email=order.shipping_email,
            order_id=str(order.id),
            order_date=order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            items=items,
            subtotal=float(order.subtotal),
            tax=float(order.tax),
            shipping=float(order.shipping_cost),
            total=float(order.total),
        )

        logger.info(f"Payment verified and order confirmed: {order.id}")

        return {
            "status": "success",
            "message": "Payment verified successfully",
            "order_id": str(order.id),
            "razorpay_payment_id": payment_data.razorpay_payment_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment verification failed",
        )


# ========== PAYMENT STATUS ENDPOINT ==========
@router.get("/{order_id}/status")
@limiter.limit(RATE_LIMIT_NORMAL)
async def get_payment_status(
    request,  # For rate limiter
    order_id: UUID,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get payment status for an order.

    Useful for checking if payment was completed.
    """
    try:
        # ========== AUTHENTICATE USER ==========
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        token = authorization.replace("Bearer ", "")
        user = await get_current_user(token, db)

        # ========== FETCH ORDER ==========
        order = OrderService.get_order_by_id(order_id, db)

        # ========== VERIFY OWNERSHIP ==========
        if order.user_id != user.id and not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only check your own orders",
            )

        return {
            "order_id": str(order.id),
            "payment_status": order.payment_status.value,
            "order_status": order.status.value,
            "razorpay_payment_id": order.razorpay_payment_id,
            "total_amount": float(order.total),
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Payment status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment status",
        )
