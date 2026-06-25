from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from core.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    phone = Column(String(20), nullable=False)

    # M-Pesa Daraja fields
    checkout_request_id = Column(String(100), nullable=True)
    merchant_request_id = Column(String(100), nullable=True)
    mpesa_receipt_number = Column(String(50), nullable=True)
    transaction_date = Column(String(20), nullable=True)

    # Result
    result_code = Column(Integer, nullable=True)
    result_desc = Column(Text, nullable=True)
    status = Column(String(20), default=PaymentStatus.PENDING.value, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
