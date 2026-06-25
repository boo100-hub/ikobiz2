from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from core.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAID = "PAID"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total = Column(Float, nullable=False)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)

    # Fulfillment
    fulfillment_method = Column(String(20), nullable=True)       # "pickup" | "seller_delivery"
    delivery_area = Column(String(200), nullable=True)
    delivery_address = Column(Text, nullable=True)
    delivery_fee = Column(Float, nullable=True, default=0)

    # Payment
    payment_method = Column(String(30), nullable=True)           # "mpesa" | "cash_on_delivery" | "bank_transfer"
    payment_status = Column(String(20), nullable=True, default="pending")

    # Customer info captured from WhatsApp
    customer_phone = Column(String(20), nullable=True)
    customer_name = Column(String(100), nullable=True)

    # Seller notes / AI summary
    seller_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    buyer = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="order", cascade="all, delete-orphan",
                            order_by="Message.created_at")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
