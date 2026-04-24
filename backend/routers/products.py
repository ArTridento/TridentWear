from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models.product import Product
from models.user import User
from schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from middleware.rate_limit import limiter, RATE_LIMIT_GENEROUS, RATE_LIMIT_NORMAL
from routers.auth import get_current_user
from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["Products"])


# ========== DEPENDENCY: VERIFY ADMIN ==========
async def verify_admin(
    authorization: Optional[str] = None,
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to verify user is admin.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = authorization.replace("Bearer ", "")
    user = await get_current_user(token, db)

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user


# ========== GET ALL PRODUCTS ==========
@router.get("", response_model=ProductListResponse)
@limiter.limit(RATE_LIMIT_GENEROUS)
async def get_all_products(
    request,  # For rate limiter
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Skip N products"),
    limit: int = Query(10, ge=1, le=100, description="Limit to N products"),
    category: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get all active products with pagination and filtering.

    Only shows active products to customers.
    """
    query = db.query(Product).filter(Product.is_active == True)

    # ========== FILTER BY CATEGORY ==========
    if category:
        query = query.filter(Product.category == category)

    # ========== SEARCH BY NAME/DESCRIPTION ==========
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_term)) |
            (Product.description.ilike(search_term)) |
            (Product.sku.ilike(search_term))
        )

    # ========== GET TOTAL COUNT ==========
    total = query.count()

    # ========== FETCH PAGINATED RESULTS ==========
    products = query.offset(skip).limit(limit).all()

    # ========== ADD DISCOUNTED PRICE ==========
    for product in products:
        product.discounted_price = product.get_discounted_price()

    return ProductListResponse(
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        per_page=limit,
        items=products,
    )


# ========== GET PRODUCT BY ID ==========
@router.get("/{product_id}", response_model=ProductResponse)
@limiter.limit(RATE_LIMIT_GENEROUS)
async def get_product(
    request,  # For rate limiter
    product_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get product by ID.

    Shows only if product is active.
    """
    product = db.query(Product).filter(
        (Product.id == product_id) & (Product.is_active == True)
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.discounted_price = product.get_discounted_price()

    return product


# ========== CREATE PRODUCT (ADMIN) ==========
@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_NORMAL)
async def create_product(
    request,  # For rate limiter
    product_data: ProductCreate,
    authorization: Optional[str] = None,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Create new product (admin only).

    - SKU must be unique
    - Price must be positive
    """
    try:
        # ========== CHECK IF SKU EXISTS ==========
        existing = db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing:
            raise ValueError("SKU already exists")

        # ========== CREATE PRODUCT ==========
        product = Product(
            **product_data.model_dump()
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        logger.info(f"Product created by admin {admin.email}: {product.id}")

        product.discounted_price = product.get_discounted_price()

        return product

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Product creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product",
        )


# ========== UPDATE PRODUCT (ADMIN) ==========
@router.put("/{product_id}", response_model=ProductResponse)
@limiter.limit(RATE_LIMIT_NORMAL)
async def update_product(
    request,  # For rate limiter
    product_id: UUID,
    product_data: ProductUpdate,
    authorization: Optional[str] = None,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Update product (admin only).

    Only updates provided fields.
    """
    try:
        # ========== FETCH PRODUCT ==========
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        # ========== UPDATE FIELDS ==========
        for field, value in product_data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)

        logger.info(f"Product updated by admin {admin.email}: {product_id}")

        product.discounted_price = product.get_discounted_price()

        return product

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product",
        )


# ========== DELETE PRODUCT (ADMIN) ==========
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMIT_NORMAL)
async def delete_product(
    request,  # For rate limiter
    product_id: UUID,
    authorization: Optional[str] = None,
    admin: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Delete product (admin only).

    Hard deletes from database. Be careful!
    """
    try:
        # ========== FETCH PRODUCT ==========
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        # ========== DELETE ==========
        db.delete(product)
        db.commit()

        logger.info(f"Product deleted by admin {admin.email}: {product_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product",
        )


# ========== GET FEATURED PRODUCTS ==========
@router.get("/featured/list", response_model=ProductListResponse)
@limiter.limit(RATE_LIMIT_GENEROUS)
async def get_featured_products(
    request,  # For rate limiter
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Get featured products for homepage.
    """
    products = db.query(Product).filter(
        (Product.is_active == True) & (Product.is_featured == True)
    ).limit(limit).all()

    for product in products:
        product.discounted_price = product.get_discounted_price()

    return ProductListResponse(
        total=len(products),
        page=1,
        per_page=limit,
        items=products,
    )
