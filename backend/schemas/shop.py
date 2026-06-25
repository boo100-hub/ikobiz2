"""
shop.py - Pydantic schemas for shop requests and responses.
"""

from pydantic import BaseModel
from typing import Optional


class ShopCreate(BaseModel):
    name: str
    description: str | None = None
    banner_image: str | None = None
    category: str | None = None
    location_area: str | None = None
    location_gps_lat: float | None = None
    location_gps_lng: float | None = None
    fulfillment_modes: str | None = None
    delivery_radius_km: float | None = None
    delivery_fee: float | None = None
    operating_hours: str | None = None
    payment_methods: str | None = None
    pickup_address: str | None = None
    phone: str | None = None


class ShopUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    banner_image: str | None = None
    category: str | None = None
    location_area: str | None = None
    location_gps_lat: float | None = None
    location_gps_lng: float | None = None
    fulfillment_modes: str | None = None
    delivery_radius_km: float | None = None
    delivery_fee: float | None = None
    operating_hours: str | None = None
    payment_methods: str | None = None
    pickup_address: str | None = None
    phone: str | None = None


class ShopOut(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    description: str | None
    banner_image: str | None
    category: str | None
    location_area: str | None
    location_gps_lat: float | None
    location_gps_lng: float | None
    fulfillment_modes: str | None
    delivery_radius_km: float | None
    delivery_fee: float | None
    operating_hours: str | None
    payment_methods: str | None
    pickup_address: str | None
    phone: str | None

    model_config = {"from_attributes": True}
