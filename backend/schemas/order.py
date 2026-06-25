"""
order.py - Pydantic schemas for order requests and responses.
"""

from pydantic import BaseModel
from typing import Optional


class OrderStatusUpdate(BaseModel):
    status: str
    seller_notes: str | None = None


class OrderStatusUpdateResponse(BaseModel):
    order_id: int
    status: str
    message: str
