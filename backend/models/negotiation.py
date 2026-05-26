"""
negotiation.py - Offer/counter-offer model for Ikobiz listings.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class Negotiation(Base):
    __tablename__ = "negotiations"

    id = Column(Integer, primary_key=True, index=True)
    ikobiz_listing_id = Column(Integer, ForeignKey("ikobiz_listings.id"), nullable=False)
    buyer_name = Column(String(200), nullable=False)
    offer_price = Column(Float, nullable=False)
    message = Column(Text, nullable=True)
    is_counter_offer = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ikobiz_listing = relationship("IkobizListing", back_populates="negotiations")
