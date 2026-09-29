from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import Product, User, WishlistItem

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


class WishIn(BaseModel):
    product_id: int


@router.get("")
def list_wishlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(WishlistItem)
        .options(joinedload(WishlistItem.product))
        .filter(WishlistItem.user_id == user.id)
        .all()
    )
    return [
        {
            "id": i.id,
            "product_id": i.product.id,
            "name": i.product.name,
            "price": i.product.price,
            "mrp": i.product.mrp,
            "image_url": i.product.image_url,
            "rating": i.product.rating,
        }
        for i in items
    ]


@router.post("")
def add_wish(payload: WishIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(Product, payload.product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    exists = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user.id, WishlistItem.product_id == payload.product_id)
        .first()
    )
    if exists:
        return {"ok": True, "already": True}
    db.add(WishlistItem(user_id=user.id, product_id=payload.product_id))
    db.commit()
    return {"ok": True}


@router.delete("/{product_id}")
def remove_wish(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user.id, WishlistItem.product_id == product_id)
        .first()
    )
    if item:
        db.delete(item)
        db.commit()
    return {"ok": True}
