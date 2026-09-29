from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import require_admin
from app.models import Order, Product, User
from app.schemas import OrderStatusIn, ProductIn, ProductOut

router = APIRouter(prefix="/api/admin", tags=["admin"])

ALLOWED_STATUS = {"pending", "confirmed", "shipped", "delivered", "cancelled"}


@router.get("/products", response_model=list[ProductOut])
def admin_products(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Product).options(joinedload(Product.category)).order_by(Product.id.desc()).all()


@router.post("/products", response_model=ProductOut)
def create_product(payload: ProductIn, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"ok": True}


@router.get("/orders")
def admin_orders(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    orders = db.query(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "total": o.total,
            "status": o.status,
            "address_text": o.address_text,
            "created_at": o.created_at.isoformat(),
            "items": [{"name": i.name, "quantity": i.quantity, "price": i.price} for i in o.items],
        }
        for o in orders
    ]


@router.patch("/orders/{order_id}")
def update_order_status(
    order_id: int,
    payload: OrderStatusIn,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    return {"ok": True, "status": order.status}
