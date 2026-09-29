from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str | None = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    brand: str
    price: float
    mrp: float
    image_url: str
    stock: int
    featured: bool
    rating: float
    review_count: int
    category_id: int
    category: CategoryOut | None = None

    model_config = {"from_attributes": True}


class ProductIn(BaseModel):
    name: str
    description: str = ""
    brand: str = ""
    price: float
    mrp: float
    image_url: str = ""
    stock: int = 0
    featured: bool = False
    category_id: int


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartQtyIn(BaseModel):
    quantity: int = Field(ge=1)


class AddressIn(BaseModel):
    full_name: str
    phone: str
    line1: str
    city: str
    state: str
    pincode: str
    is_default: bool = False


class AddressOut(BaseModel):
    id: int
    full_name: str
    phone: str
    line1: str
    city: str
    state: str
    pincode: str
    is_default: bool

    model_config = {"from_attributes": True}


class CheckoutIn(BaseModel):
    address_id: int


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class ReviewOut(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    comment: str
    created_at: datetime
    user_name: str = ""

    model_config = {"from_attributes": True}


class OrderStatusIn(BaseModel):
    status: str
