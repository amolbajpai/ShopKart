from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Category, Product
from app.schemas import CategoryOut, ProductOut

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.get("/products", response_model=list[ProductOut])
def list_products(
    q: str | None = None,
    category: str | None = None,
    featured: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = Query("featured", pattern="^(featured|price_asc|price_desc|rating)$"),
    db: Session = Depends(get_db),
):
    query = db.query(Product).options(joinedload(Product.category))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Product.name.ilike(like), Product.brand.ilike(like), Product.description.ilike(like))
        )
    if category:
        query = query.join(Category).filter(Category.slug == category)
    if featured is True:
        query = query.filter(Product.featured.is_(True))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "rating":
        query = query.order_by(Product.rating.desc())
    else:
        query = query.order_by(Product.featured.desc(), Product.rating.desc())
    return query.all()


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
