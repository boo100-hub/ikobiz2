"""
shop.py - Shop model with owner relationship and fulfillment/operations fields.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from core.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    banner_image = Column(String(500), nullable=True)

    # Fulfillment & operations
    category = Column(String(100), nullable=True)
    location_area = Column(String(200), nullable=True)
    location_gps_lat = Column(Float, nullable=True)
    location_gps_lng = Column(Float, nullable=True)
    fulfillment_modes = Column(String(100), nullable=True)       # "pickup,seller_delivery"
    delivery_radius_km = Column(Float, nullable=True, default=0)
    delivery_fee = Column(Float, nullable=True, default=0)
    operating_hours = Column(Text, nullable=True)                # JSON string e.g. {"mon-fri":"8-18"}
    payment_methods = Column(String(200), nullable=True)         # "mpesa,cash_on_delivery,bank_transfer"
    pickup_address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="owned_shops")
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
