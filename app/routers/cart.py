from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import CartItem, Product, User
from app.schemas import CartItemIn, CartQtyIn

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _item_out(item: CartItem) -> dict:
    p = item.product
    return {
        "id": item.id,
        "product_id": p.id,
        "name": p.name,
        "price": p.price,
        "mrp": p.mrp,
        "image_url": p.image_url,
        "stock": p.stock,
        "quantity": item.quantity,
        "line_total": round(p.price * item.quantity, 2),
    }


@router.get("")
def get_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.user_id == user.id)
        .all()
    )
    out = [_item_out(i) for i in items]
    return {
        "items": out,
        "count": sum(i["quantity"] for i in out),
        "subtotal": round(sum(i["line_total"] for i in out), 2),
    }


@router.post("")
def add_to_cart(payload: CartItemIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    item = (
        db.query(CartItem)
        .filter(CartItem.user_id == user.id, CartItem.product_id == payload.product_id)
        .first()
    )
    qty = payload.quantity + (item.quantity if item else 0)
    if qty > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock")
    if item:
        item.quantity = qty
    else:
        item = CartItem(user_id=user.id, product_id=payload.product_id, quantity=payload.quantity)
        db.add(item)
    db.commit()
    return {"ok": True}


@router.patch("/{item_id}")
def update_qty(item_id: int, payload: CartQtyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    product = db.get(Product, item.product_id)
    if payload.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock")
    item.quantity = payload.quantity
    db.commit()
    return {"ok": True}


@router.delete("/{item_id}")
def remove_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
