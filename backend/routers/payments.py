"""
routers/payments.py - M-Pesa payment processing via Daraja API.

POST   /payments/initiate   - Initiate STK Push to customer phone
POST   /payments/mpesa-callback  - Safaricom callback (no auth)
GET    /payments/{order_id} - Check payment status for an order
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Order, OrderStatus, Payment, PaymentStatus
from schemas.payment import InitiatePaymentRequest, InitiatePaymentResponse, PaymentStatusResponse
from services.daraja import stk_push, parse_callback

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/initiate")
async def initiate_payment(
    data: InitiatePaymentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Initiate M-Pesa STK Push for an order."""
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.buyer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only pay for your own orders")

    if order.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pay for order in '{order.status.value}' status"
        )

    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Order is already paid")

    if not data.phone.startswith("254") or len(data.phone) != 12:
        raise HTTPException(status_code=400, detail="Phone must be in 254XXXXXXXXX format")

    # Check for existing pending payment
    existing = db.query(Payment).filter(
        Payment.order_id == order.id,
        Payment.status == PaymentStatus.PENDING.value,
    ).first()
    if existing:
        return InitiatePaymentResponse(
            success=True,
            checkout_request_id=existing.checkout_request_id,
            message="Payment already initiated. Check your phone for M-Pesa prompt.",
        )

    try:
        resp = await stk_push(
            phone=data.phone,
            amount=order.total,
            account_ref=f"IKO{order.id}",
            transaction_desc=f"Ikobiz Order {order.id}",
        )
    except Exception as e:
        logger.error(f"STK Push failed for order #{order.id}: {e}")
        raise HTTPException(status_code=502, detail="Payment service unavailable. Try again later.")

    result_code = resp.get("ResponseCode")
    if result_code != "0":
        raise HTTPException(
            status_code=400,
            detail=f"Payment failed: {resp.get('responseDescription', resp.get('errorMessage', 'Unknown error'))}"
        )

    payment = Payment(
        order_id=order.id,
        amount=order.total,
        phone=data.phone,
        checkout_request_id=resp.get("CheckoutRequestID"),
        merchant_request_id=resp.get("MerchantRequestID"),
        status=PaymentStatus.PENDING.value,
    )
    db.add(payment)
    db.commit()

    return InitiatePaymentResponse(
        success=True,
        checkout_request_id=payment.checkout_request_id,
        message="M-Pesa prompt sent. Check your phone and enter your PIN to complete payment.",
    )


@router.post("/mpesa-callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    """Safaricom STK Push callback endpoint (no auth required)."""
    body = await request.body()
    try:
        result = parse_callback(body)
    except Exception as e:
        logger.error(f"Failed to parse M-Pesa callback: {e}")
        return {"ResultCode": 1, "ResultDesc": "Invalid payload"}

    checkout_request_id = result.get("checkout_request_id")
    if not checkout_request_id:
        return {"ResultCode": 1, "ResultDesc": "Missing CheckoutRequestID"}

    payment = db.query(Payment).filter(
        Payment.checkout_request_id == checkout_request_id,
    ).first()
    if not payment:
        logger.warning(f"No payment record for CheckoutRequestID: {checkout_request_id}")
        return {"ResultCode": 1, "ResultDesc": "Payment not found"}

    payment.result_code = result.get("result_code")
    payment.result_desc = result.get("result_desc")

    if result.get("result_code") == 0:
        payment.status = PaymentStatus.COMPLETED.value
        payment.mpesa_receipt_number = result.get("mpesa_receipt_number")
        payment.transaction_date = result.get("transaction_date")

        # Update order status and payment_status
        order = db.query(Order).filter(Order.id == payment.order_id).first()
        if order:
            order.status = OrderStatus.PAID
            order.payment_status = "paid"

            # Notify buyer via WhatsApp
            if order.customer_phone:
                try:
                    from app.whatsapp.service import send_text_message_sync
                    send_text_message_sync(
                        order.customer_phone,
                        f"💰 *Payment Received!*\n\n"
                        f"Order #{order.id}\n"
                        f"Amount: KSh {order.total:,.0f}\n"
                        f"M-Pesa Receipt: {result.get('mpesa_receipt_number', 'N/A')}\n\n"
                        f"Your order is now being processed. 🚀\n"
                        f"View: {settings.SITE_URL}/checkout/{order.id}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send payment confirmation to buyer: {e}")

            # Notify seller
            for oi in order.items:
                if oi.product_id and oi.product and oi.product.shop and oi.product.shop.owner_id:
                    from core.config import settings
                    seller = db.query(User).filter(User.id == oi.product.shop.owner_id).first()
                    if seller and seller.phone:
                        try:
                            send_text_message_sync(
                                seller.phone,
                                f"💰 *Payment Confirmed!*\n\n"
                                f"Order #{order.id}\n"
                                f"KSh {order.total:,.0f}\n"
                                f"Receipt: {result.get('mpesa_receipt_number', 'N/A')}\n\n"
                                f"Prepare the order for dispatch. 🚚"
                            )
                        except Exception:
                            pass
                    break
    else:
        payment.status = PaymentStatus.FAILED.value

    db.commit()
    logger.info(f"M-Pesa callback processed: {checkout_request_id}, code={result.get('result_code')}")

    return {"ResultCode": 0, "ResultDesc": "Success"}


@router.get("/{order_id}")
def payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Check payment status for an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.buyer_id != user.id and user.role != "admin":
        # Check if seller
        is_seller = False
        for oi in order.items:
            if oi.product_id and oi.product and oi.product.shop and oi.product.shop.owner_id == user.id:
                is_seller = True
                break
        if not is_seller:
            raise HTTPException(status_code=403, detail="Access denied")

    payment = db.query(Payment).filter(Payment.order_id == order.id).order_by(Payment.created_at.desc()).first()

    return PaymentStatusResponse(
        order_id=order.id,
        payment_status=order.payment_status or "pending",
        amount=order.total,
        mpesa_receipt_number=payment.mpesa_receipt_number if payment else None,
        message="Payment verified" if order.payment_status == "paid" else "Awaiting payment",
    )
