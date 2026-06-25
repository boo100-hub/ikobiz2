"""
product.py - Product model with status enum, shop relationship, category and attributes.
"""

from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from core.database import Base


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    OUT_OF_STOCK = "out_of_stock"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    image_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    attributes = Column(Text, nullable=True)                     # JSON string e.g. {"color":"black","size":"42"}
    status = Column(SAEnum(ProductStatus), default=ProductStatus.ACTIVE, nullable=False)

    # Type: "physical" or "service"
    product_type = Column(String(20), default="physical", nullable=False)
    service_duration_minutes = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    shop = relationship("Shop", back_populates="products")
