from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Product, Review, User
from app.schemas import ReviewIn, ReviewOut

router = APIRouter(prefix="/api/products", tags=["reviews"])


@router.get("/{product_id}/reviews", response_model=list[ReviewOut])
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )
    out = []
    for r in reviews:
        item = ReviewOut.model_validate(r)
        item.user_name = r.user.full_name or r.user.email
        out.append(item)
    return out


@router.post("/{product_id}/reviews", response_model=ReviewOut)
def add_review(
    product_id: int,
    payload: ReviewIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    existing = (
        db.query(Review).filter(Review.user_id == user.id, Review.product_id == product_id).first()
    )
    if existing:
        existing.rating = payload.rating
        existing.comment = payload.comment
        review = existing
    else:
        review = Review(
            user_id=user.id,
            product_id=product_id,
            rating=payload.rating,
            comment=payload.comment,
        )
        db.add(review)
    db.flush()
    rows = db.query(Review).filter(Review.product_id == product_id).all()
    product.review_count = len(rows)
    product.rating = round(sum(r.rating for r in rows) / len(rows), 1)
    db.commit()
    db.refresh(review)
    out = ReviewOut.model_validate(review)
    out.user_name = user.full_name or user.email
    return out
