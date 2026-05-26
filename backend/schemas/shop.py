"""
shop.py - Pydantic schemas for shop requests and responses.
"""

from pydantic import BaseModel


class ShopCreate(BaseModel):
    name: str
    description: str | None = None
    banner_image: str | None = None


class ShopUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    banner_image: str | None = None


class ShopOut(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    description: str | None
    banner_image: str | None

    model_config = {"from_attributes": True}
