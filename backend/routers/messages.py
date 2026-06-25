import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Order, OrderItem, OrderStatus, Message, Shop, Product
from app.whatsapp.service import send_text_message_sync

logger = logging.getLogger(__name__)

router = APIRouter(tags=["messages"])


class SendMessageRequest(BaseModel):
    content: str


def _notify_via_whatsapp(phone: str | None, message: str):
    if phone:
        try:
            send_text_message_sync(phone, message)
        except Exception:
            logger.warning(f"Failed to send WhatsApp notification to {phone}")


def _generate_auto_replies(db: Session, order: Order, user: User):
    shop_name = None
    seller = None
    item_details = []

    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop:
                shop_name = product.shop.name
                seller = db.query(User).filter(User.id == product.shop.owner_id).first()
                item_details.append(f"{product.title} x{oi.quantity} — KSh {oi.price * oi.quantity:,.0f}")

    store_label = shop_name or "Ikobiz Platform"
    items_str = "; ".join(item_details) if item_details else "See order for details"

    if seller:
        buyer_msg = Message(
            order_id=order.id,
            sender_id=seller.id,
            content=(
                f"Thank you for shopping at {store_label}! "
                f"Your order #{order.id} has been received. "
                f"The seller has been notified and your order is being prepared for shipping. "
                f"We appreciate your business!"
            ),
            is_auto_reply=True,
        )
        db.add(buyer_msg)

        if user.phone:
            _notify_via_whatsapp(
                user.phone,
                f"🛒 Order #{order.id} Confirmed!\n"
                f"Thank you for shopping at {store_label}.\n"
                f"Your order is being prepared for shipping.\n"
                f"Total: KSh {order.total:,.0f}\n"
                f"View: {settings.SITE_URL}/checkout/{order.id}"
            )

        seller_msg = Message(
            order_id=order.id,
            sender_id=user.id,
            content=(
                f"New Order #{order.id} from {user.username}!\n"
                f"Items: {items_str}\n"
                f"Total: KSh {order.total:,.0f}\n"
                f"Buyer: {user.username}\n"
                f"Please prepare the order for shipping."
            ),
            is_auto_reply=True,
        )
        db.add(seller_msg)

        if seller.phone:
            _notify_via_whatsapp(
                seller.phone,
                f"📦 New Order #{order.id}!\n"
                f"From: {user.username}\n"
                f"Items: {items_str}\n"
                f"Total: KSh {order.total:,.0f}\n"
                f"Prepare for shipping."
            )

    db.commit()


@router.get("/orders/{order_id}/messages")
def get_order_messages(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_buyer = order.buyer_id == user.id
    is_seller = _is_seller_for_order(db, order, user.id)

    if not is_buyer and not is_seller:
        raise HTTPException(status_code=403, detail="Not authorized to view these messages")

    messages = db.query(Message).filter(Message.order_id == order_id).order_by(Message.created_at).all()
    return [
        {
            "id": m.id,
            "order_id": m.order_id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.username if m.sender else "Unknown",
            "content": m.content,
            "is_auto_reply": m.is_auto_reply,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.post("/orders/{order_id}/messages")
def send_order_message(
    order_id: int,
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_buyer = order.buyer_id == user.id
    is_seller = _is_seller_for_order(db, order, user.id)

    if not is_buyer and not is_seller:
        raise HTTPException(status_code=403, detail="Not authorized to send messages for this order")

    recipient_id = None
    if is_buyer:
        recipient_id = _get_seller_for_order(db, order)
    elif is_seller:
        recipient_id = order.buyer_id

    msg = Message(
        order_id=order_id,
        sender_id=user.id,
        content=data.content.strip(),
        is_auto_reply=False,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    if recipient_id:
        recipient = db.query(User).filter(User.id == recipient_id).first()
        if recipient and recipient.phone:
            _notify_via_whatsapp(
                recipient.phone,
                f"💬 New message on Order #{order_id}\n"
                f"From: {user.username}\n"
                f"{data.content.strip()[:200]}"
            )

    return {
        "id": msg.id,
        "order_id": msg.order_id,
        "sender_id": msg.sender_id,
        "sender_name": user.username,
        "content": msg.content,
        "is_auto_reply": msg.is_auto_reply,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }


def _is_seller_for_order(db: Session, order: Order, user_id: int) -> bool:
    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop and product.shop.owner_id == user_id:
                return True
    return False


def _get_seller_for_order(db: Session, order: Order) -> int | None:
    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop:
                return product.shop.owner_id
    return None
