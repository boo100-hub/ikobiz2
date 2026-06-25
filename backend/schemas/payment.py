from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InitiatePaymentRequest(BaseModel):
    order_id: int
    phone: str  # 254XXXXXXXXX


class InitiatePaymentResponse(BaseModel):
    success: bool
    checkout_request_id: Optional[str] = None
    message: str


class PaymentStatusResponse(BaseModel):
    order_id: int
    payment_status: str
    amount: float
    mpesa_receipt_number: Optional[str] = None
    message: str


class PaymentCallback(BaseModel):
    """Raw Safaricom callback payload."""
    Body: dict
