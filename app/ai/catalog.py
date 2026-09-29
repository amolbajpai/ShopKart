from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import Category, Product


def catalog_snapshot() -> str:
    db = SessionLocal()
    try:
        products = (
            db.query(Product).options(joinedload(Product.category)).order_by(Product.id).all()
        )
        if not products:
            return "(catalog is empty)"
        lines = []
        for p in products:
            cat = p.category.name if p.category else ""
            lines.append(
                f"- #{p.id} {p.name} | {p.brand} | {cat} | ₹{p.price} "
                f"(MRP ₹{p.mrp}) | stock {p.stock} | rating {p.rating}/5 "
                f"({p.review_count} ratings) | /product/{p.id}"
            )
        cats = db.query(Category).order_by(Category.name).all()
        cat_line = ", ".join(f"{c.name} ({c.slug})" for c in cats)
        return f"Categories: {cat_line}\nProducts:\n" + "\n".join(lines)
    finally:
        db.close()
