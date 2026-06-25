"""
user.py - User model for authentication and role management.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="buyer")  # buyer | seller | admin
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # A seller can own many shops
    owned_shops = relationship("Shop", back_populates="owner", cascade="all, delete-orphan")
