"""Read-only catalog tools. Nothing here writes to the database."""

from __future__ import annotations

import json

from langchain_core.tools import tool
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.ai.prompts import STORE_FACTS
from app.database import SessionLocal
from app.models import Category, Product, Review


def _product_card(product: Product) -> dict:
    category = product.category.name if product.category else ""
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "category": category,
        "price": product.price,
        "mrp": product.mrp,
        "stock": product.stock,
        "in_stock": product.stock > 0,
        "rating": product.rating,
        "review_count": product.review_count,
        "featured": product.featured,
        "description": product.description,
        "page": f"/product/{product.id}",
    }


def _dumps(data: object) -> str:
    return json.dumps(data, ensure_ascii=False)


@tool
def search_products(
    query: str,
    category: str = "",
    min_price: float = 0,
    max_price: float = 0,
    sort: str = "featured",
) -> str:
    """Search ShopKart products by name, brand, or description. Optional category slug (electronics, fashion, home, books, beauty, sports, grocery), price range in INR, and sort: featured, price_asc, price_desc, rating."""
    db = SessionLocal()
    try:
        q = db.query(Product).options(joinedload(Product.category))
        if query:
            like = f"%{query.strip()}%"
            q = q.filter(
                or_(Product.name.ilike(like), Product.brand.ilike(like), Product.description.ilike(like))
            )
        if category:
            q = q.join(Category).filter(Category.slug == category.strip().lower())
        if min_price and min_price > 0:
            q = q.filter(Product.price >= min_price)
        if max_price and max_price > 0:
            q = q.filter(Product.price <= max_price)
        if sort == "price_asc":
            q = q.order_by(Product.price.asc())
        elif sort == "price_desc":
            q = q.order_by(Product.price.desc())
        elif sort == "rating":
            q = q.order_by(Product.rating.desc())
        else:
            q = q.order_by(Product.featured.desc(), Product.rating.desc())
        items = q.limit(8).all()
        if not items:
            return _dumps({"results": [], "message": "No matching products in the catalog."})
        return _dumps({"results": [_product_card(p) for p in items]})
    finally:
        db.close()


@tool
def get_product_details(product_id: int) -> str:
    """Get full details for one product by its numeric id."""
    db = SessionLocal()
    try:
        product = (
            db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()
        )
        if not product:
            return _dumps({"error": "Product not found"})
        return _dumps(_product_card(product))
    finally:
        db.close()


@tool
def list_categories() -> str:
    """List all ShopKart categories with how many products each has."""
    db = SessionLocal()
    try:
        cats = db.query(Category).order_by(Category.name).all()
        return _dumps(
            [
                {
                    "id": c.id,
                    "name": c.name,
                    "slug": c.slug,
                    "product_count": len(c.products),
                }
                for c in cats
            ]
        )
    finally:
        db.close()


@tool
def get_product_reviews(product_id: int) -> str:
    """Read customer reviews and ratings for a product. Does not add or change reviews."""
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            return _dumps({"error": "Product not found"})
        reviews = (
            db.query(Review)
            .filter(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .limit(8)
            .all()
        )
        return _dumps(
            {
                "product_id": product_id,
                "average_rating": product.rating,
                "review_count": product.review_count,
                "reviews": [
                    {
                        "rating": r.rating,
                        "comment": r.comment,
                        "user": r.user.full_name or r.user.email,
                    }
                    for r in reviews
                ],
            }
        )
    finally:
        db.close()


@tool
def compare_products(product_id_a: int, product_id_b: int) -> str:
    """Compare two catalog products side by side using their ids."""
    db = SessionLocal()
    try:
        ids = [product_id_a, product_id_b]
        products = (
            db.query(Product).options(joinedload(Product.category)).filter(Product.id.in_(ids)).all()
        )
        found = {p.id: _product_card(p) for p in products}
        missing = [i for i in ids if i not in found]
        if missing:
            return _dumps({"error": "Product not found", "missing_ids": missing})
        return _dumps({"a": found[product_id_a], "b": found[product_id_b]})
    finally:
        db.close()


@tool
def get_store_info(topic: str = "about") -> str:
    """ShopKart store facts: about, shopping, delivery, returns, accounts, assistant. Use this for store policy questions, not product specs."""
    key = (topic or "about").strip().lower()
    if key not in STORE_FACTS:
        key = "about"
    return _dumps({"topic": key, "info": STORE_FACTS[key], "store": STORE_FACTS["name"]})


RAVI_TOOLS = [
    search_products,
    get_product_details,
    list_categories,
    get_product_reviews,
    compare_products,
    get_store_info,
]
