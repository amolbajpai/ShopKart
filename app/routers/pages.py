from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings

router = APIRouter(tags=["pages"])
_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent.parent / "templates"),
    autoescape=select_autoescape(["html"]),
)


def _page(request: Request, name: str, **extra):
    html = _env.get_template(name).render(request=request, app_name=settings.app_name, **extra)
    return HTMLResponse(html)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _page(request, "index.html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return _page(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return _page(request, "register.html")


@router.get("/product/{product_id}", response_class=HTMLResponse)
def product_page(request: Request, product_id: int):
    return _page(request, "product.html", product_id=product_id)


@router.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request):
    return _page(request, "cart.html")


@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request):
    return _page(request, "checkout.html")


@router.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request):
    return _page(request, "orders.html")


@router.get("/orders/{order_id}", response_class=HTMLResponse)
def order_detail_page(request: Request, order_id: int):
    return _page(request, "order_detail.html", order_id=order_id)


@router.get("/wishlist", response_class=HTMLResponse)
def wishlist_page(request: Request):
    return _page(request, "wishlist.html")


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request):
    return _page(request, "profile.html")


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return _page(request, "admin.html")
