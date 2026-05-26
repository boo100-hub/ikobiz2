from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from core.database import Base


class IkobizListingStatus(str, enum.Enum):
    OPEN = "OPEN"
    NEGOTIATING = "NEGOTIATING"
    SOLD = "SOLD"
    CLOSED = "CLOSED"


class IkobizListing(Base):
    __tablename__ = "ikobiz_listings"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    seller_name = Column(String(200), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    starting_price = Column(Float, nullable=False)
    buy_now_price = Column(Float, nullable=True)
    quantity = Column(Integer, default=1)
    image_url = Column(String(500), nullable=True)
    status = Column(SAEnum(IkobizListingStatus), default=IkobizListingStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    negotiations = relationship("Negotiation", back_populates="ikobiz_listing", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="listing", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="listing", cascade="all, delete-orphan")
