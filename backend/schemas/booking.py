from pydantic import BaseModel
from datetime import date, time


class BookingCreate(BaseModel):
    service_id: int
    scheduled_date: date
    scheduled_time: time
    location_type: str = "at_seller"
    location_address: str | None = None
    customer_notes: str | None = None


class BookingUpdate(BaseModel):
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    status: str | None = None
    seller_notes: str | None = None


class BookingOut(BaseModel):
    id: int
    service_id: int
    buyer_id: int
    seller_id: int
    shop_id: int
    scheduled_date: date
    scheduled_time: time
    duration_minutes: int | None = None
    location_type: str
    location_address: str | None = None
    price: float
    status: str
    customer_phone: str | None = None
    customer_name: str | None = None
    seller_notes: str | None = None
    customer_notes: str | None = None
    created_at: str | None = None

    service_title: str | None = None
    shop_name: str | None = None

    model_config = {"from_attributes": True}
