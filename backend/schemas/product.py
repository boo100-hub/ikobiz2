"""
product.py - Pydantic schemas for product requests and responses.
"""

from pydantic import BaseModel


class ProductCreate(BaseModel):
    title: str
    description: str | None = None
    price: float
    stock: int = 0
    image_url: str | None = None
    category: str | None = None
    attributes: str | None = None
    status: str = "active"
    product_type: str = "physical"
    service_duration_minutes: int | None = None


class ProductUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: float | None = None
    stock: int | None = None
    image_url: str | None = None
    category: str | None = None
    attributes: str | None = None
    status: str | None = None
    product_type: str | None = None
    service_duration_minutes: int | None = None


class ProductOut(BaseModel):
    id: int
    shop_id: int
    title: str
    description: str | None
    price: float
    stock: int
    image_url: str | None
    category: str | None
    attributes: str | None
    status: str
    product_type: str = "physical"
    service_duration_minutes: int | None = None

    model_config = {"from_attributes": True}
