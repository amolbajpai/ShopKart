from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import Address, CartItem, Order, OrderItem, User
from app.schemas import CheckoutIn

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _order_out(order: Order) -> dict:
    return {
        "id": order.id,
        "total": order.total,
        "status": order.status,
        "address_text": order.address_text,
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "name": i.name,
                "price": i.price,
                "quantity": i.quantity,
                "line_total": round(i.price * i.quantity, 2),
            }
            for i in order.items
        ],
    }


@router.get("")
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [_order_out(o) for o in orders]


@router.get("/{order_id}")
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_out(order)


@router.post("")
def checkout(payload: CheckoutIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.query(Address).filter(Address.id == payload.address_id, Address.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=400, detail="Address not found")
    cart = (
        db.query(CartItem)
        .options(joinedload(CartItem.product))
        .filter(CartItem.user_id == user.id)
        .all()
    )
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = 0.0
    for item in cart:
        if item.quantity > item.product.stock:
            raise HTTPException(status_code=400, detail=f"{item.product.name} is out of stock")
        total += item.product.price * item.quantity

    address_text = (
        f"{address.full_name}, {address.phone}, {address.line1}, "
        f"{address.city}, {address.state} - {address.pincode}"
    )
    order = Order(user_id=user.id, address_text=address_text, total=round(total, 2), status="confirmed")
    db.add(order)
    db.flush()
    for item in cart:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
        )
        item.product.stock -= item.quantity
        db.delete(item)
    db.commit()
    db.refresh(order)
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order.id).first()
    return _order_out(order)
