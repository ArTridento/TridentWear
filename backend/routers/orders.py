from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.order import Order
from schemas.order import OrderCreate, OrderResponse, OrderListResponse
from services.order_service import OrderService
from services.email_service import EmailService
from middleware.rate_limit import limiter, RATE_LIMIT_NORMAL
from routers.auth import get_current_user
from typing import Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


# ========== CREATE ORDER ==========
@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_NORMAL)
async def create_order(
    request,  # For rate limiter
    order_data: OrderCreate,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Create a new order.

    CRITICAL SECURITY:
    - Never trusts frontend prices
    - Fetches current prices from database
    - Validates stock
    - Calculates totals on backend only

    Returns order with Razorpay order ID for payment.
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

        # ========== VALIDATE ORDER ITEMS (BACKEND PRICES ONLY) ==========
        validated_items = OrderService.validate_order_items(order_data.items, db)

        # ========== CALCULATE ORDER TOTALS ==========
        totals = OrderService.calculate_order_totals(validated_items)

        # ========== CREATE ORDER ==========
        order = OrderService.create_order(
            user_id=user.id,
            order_data=order_data,
            validated_items=validated_items,
            totals=totals,
            db=db,
        )

        logger.info(f"Order created: {order.id} for user {user.id}")

        # ========== CREATE RAZORPAY ORDER (handled in payments router) ==========
        # The frontend will call /api/payments/create-order next

        return order

    except ValueError as e:
        logger.warning(f"Order creation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )


# ========== GET USER'S ORDERS ==========
@router.get("", response_model=OrderListResponse)
@limiter.limit(RATE_LIMIT_NORMAL)
async def get_user_orders(
    request,  # For rate limiter
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get all orders for the authenticated user.

    Includes pagination.
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

        # ========== FETCH ORDERS ==========
        orders, total = OrderService.get_user_orders(user.id, db, skip, limit)

        return OrderListResponse(
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            per_page=limit,
            items=orders,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders",
        )


# ========== GET ORDER BY ID ==========
@router.get("/{order_id}", response_model=OrderResponse)
@limiter.limit(RATE_LIMIT_NORMAL)
async def get_order(
    request,  # For rate limiter
    order_id: UUID,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get order by ID (owner only).

    Users can only see their own orders.
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
                detail="You can only view your own orders",
            )

        return order

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order fetch error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order",
        )


# ========== CANCEL ORDER ==========
@router.post("/{order_id}/cancel")
@limiter.limit(RATE_LIMIT_NORMAL)
async def cancel_order(
    request,  # For rate limiter
    order_id: UUID,
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Cancel an order (only if not paid).

    Users can only cancel their own orders.
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
                detail="You can only cancel your own orders",
            )

        # ========== CANCEL ORDER ==========
        cancelled_order = OrderService.cancel_order(order_id, db)

        return {
            "status": "success",
            "message": "Order cancelled successfully",
            "order_id": str(cancelled_order.id),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order cancellation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order",
        )
