from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Request, status

from app.db.json_manager import read_json, update_json
from app.services.auth_service import get_session_user
from app.services.product_service import load_products

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
REVIEWS_PATH = str(BASE_DIR / "db" / "reviews.json")


def _load_reviews() -> List[Dict[str, Any]]:
    reviews = read_json(REVIEWS_PATH)
    return reviews if isinstance(reviews, list) else []


def _product_exists(product_id: int) -> bool:
    return any(int(product.get("id", 0)) == int(product_id) for product in load_products())


def get_product_reviews(product_id: int) -> Dict[str, Any]:
    reviews = [
        review for review in _load_reviews()
        if int(review.get("product_id", 0)) == int(product_id)
        and review.get("status", "approved") == "approved"
    ]
    counts = {star: 0 for star in range(1, 6)}
    for review in reviews:
        rating = int(review.get("rating", 0))
        if rating in counts:
            counts[rating] += 1
    average = round(sum(int(r.get("rating", 0)) for r in reviews) / len(reviews), 1) if reviews else 0
    return {
        "product_id": product_id,
        "count": len(reviews),
        "average": average,
        "bars": counts,
        "reviews": sorted(reviews, key=lambda item: item.get("created_at", ""), reverse=True),
    }


def create_product_review(payload: Any, request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please sign in to review.")
    product_id = int(payload.product_id)
    rating = int(payload.rating)
    review_text = str(payload.review or "").strip()
    if not _product_exists(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5.")
    if len(review_text) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review must be at least 8 characters.")

    created = None

    def _insert(reviews: list):
        nonlocal created
        reviews = reviews if isinstance(reviews, list) else []
        if any(int(r.get("user_id", 0)) == int(user["id"]) and int(r.get("product_id", 0)) == product_id for r in reviews):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already reviewed this product.")
        created = {
            "id": max([int(r.get("id", 0)) for r in reviews] or [0]) + 1,
            "product_id": product_id,
            "user_id": user["id"],
            "user_name": user.get("name", "Trident member"),
            "rating": rating,
            "review": review_text,
            "verified_purchase": False,
            "status": "pending_moderation",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        reviews.append(created)
        return reviews

    update_json(REVIEWS_PATH, _insert)
    return {"success": True, "message": "Review submitted for moderation.", "review": created}


def get_admin_reviews(status_filter: Optional[str] = None) -> Dict[str, Any]:
    reviews = _load_reviews()
    if status_filter:
        normalized = normalize_review_status(status_filter)
        reviews = [review for review in reviews if normalize_review_status(review.get("status", "pending")) == normalized]

    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for review in _load_reviews():
        status_value = normalize_review_status(review.get("status", "pending"))
        if status_value in counts:
            counts[status_value] += 1

    return {
        "success": True,
        "counts": counts,
        "reviews": sorted(reviews, key=lambda item: item.get("created_at", ""), reverse=True),
    }


def normalize_review_status(value: Any) -> str:
    status_value = str(value or "pending").strip().lower().replace("_moderation", "")
    if status_value in {"pending", "approved", "rejected"}:
        return status_value
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review status must be pending, approved, or rejected.")


def moderate_review(review_id: int, status_value: str, notes: Optional[str], admin: Dict[str, Any]) -> Dict[str, Any]:
    normalized_status = normalize_review_status(status_value)
    updated_review = None

    def _update(reviews: list):
        nonlocal updated_review
        reviews = reviews if isinstance(reviews, list) else []
        for review in reviews:
            if int(review.get("id", 0)) == int(review_id):
                review["status"] = normalized_status
                review["moderation_notes"] = str(notes or "").strip()
                review["moderated_by"] = admin.get("id")
                review["moderated_at"] = datetime.now(timezone.utc).isoformat()
                updated_review = review
                break
        return reviews

    update_json(REVIEWS_PATH, _update)
    if not updated_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return {"success": True, "message": f"Review {normalized_status}.", "review": updated_review}


def delete_review(review_id: int) -> Dict[str, Any]:
    deleted = False

    def _delete(reviews: list):
        nonlocal deleted
        reviews = reviews if isinstance(reviews, list) else []
        remaining = []
        for review in reviews:
            if int(review.get("id", 0)) == int(review_id):
                deleted = True
            else:
                remaining.append(review)
        return remaining

    update_json(REVIEWS_PATH, _delete)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    return {"success": True, "message": "Review deleted."}
