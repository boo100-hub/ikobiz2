import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Product, ProductStatus, CartItem, Order, OrderItem, OrderStatus, Message, Shop
from app.whatsapp.service import send_text_message_sync
from schemas.order import OrderStatusUpdate, OrderStatusUpdateResponse
from models import Payment, PaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cart"])


class CartAddRequest(BaseModel):
    product_id: Optional[int] = None
    quantity: int = 1


class CheckoutRequest(BaseModel):
    fulfillment_method: Optional[str] = None   # "seller_delivery" | "pickup"
    delivery_area: Optional[str] = None
    delivery_address: Optional[str] = None
    payment_method: Optional[str] = None       # "mpesa" | "cash_on_delivery"
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None


# ---------- Cart ----------


@router.get("/cart")
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    result = []
    for ci in items:
        if not ci.product_id:
            continue
        product = ci.product
        entry = {
            "id": ci.id,
            "quantity": ci.quantity,
            "added_at": ci.added_at.isoformat() if ci.added_at else None,
            "type": "shop_product",
            "listing": None,
            "product": {
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "image_url": product.image_url,
                "shop_name": product.shop.name if product.shop else None,
                "shop_slug": product.shop.slug if product.shop else None,
                "status": product.status.value if product.status else "active",
            } if product else None,
        }
        result.append(entry)
    return result


@router.post("/cart")
def add_to_cart(
    data: CartAddRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.product_id:
        raise HTTPException(status_code=400, detail="Provide product_id")

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.status != ProductStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="This product is not available")
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} available")

    existing = db.query(CartItem).filter(
        CartItem.user_id == user.id,
        CartItem.product_id == data.product_id,
    ).first()
    if existing:
        existing.quantity += data.quantity
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(user_id=user.id, product_id=data.product_id, quantity=data.quantity)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/cart/{item_id}")
def remove_cart_item_by_id(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item removed from cart"}


@router.delete("/cart")
def remove_cart_item_by_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.query(CartItem).filter(CartItem.product_id == product_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item removed from cart"}


@router.patch("/cart")
def update_cart_item(
    data: CartAddRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not data.product_id:
        raise HTTPException(status_code=400, detail="Provide product_id")

    item = db.query(CartItem).filter(
        CartItem.user_id == user.id,
        CartItem.product_id == data.product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    product = db.query(Product).filter(Product.id == data.product_id).first()
    if product and product.stock < data.quantity:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} available")

    item.quantity = data.quantity
    db.commit()
    db.refresh(item)
    return item


# ---------- Checkout / Orders ----------


def _notify_via_whatsapp(phone: str | None, message: str):
    if phone:
        try:
            send_text_message_sync(phone, message)
        except Exception:
            logger.warning(f"Failed to send WhatsApp notification to {phone}")


@router.post("/checkout")
def checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = 0.0
    order_items_data = []
    notified_sellers = set()

    for ci in cart_items:
        if not ci.product_id:
            continue
        product = ci.product
        if not product or product.status != ProductStatus.ACTIVE:
            raise HTTPException(status_code=400, detail=f"'{product.title if product else 'Item'}' is no longer available")
        if product.stock < ci.quantity:
            raise HTTPException(status_code=400, detail=f"Only {product.stock} of '{product.title}' available")
        line_total = product.price * ci.quantity
        total += line_total
        order_items_data.append({
            "type": "product",
            "product": product,
            "price": product.price,
            "quantity": ci.quantity,
        })
        shop = product.shop
        if shop and shop.owner_id and shop.owner_id not in notified_sellers:
            seller = db.query(User).filter(User.id == shop.owner_id).first()
            if seller and seller.phone:
                _notify_via_whatsapp(
                    seller.phone,
                    f"📦 New Order!\n"
                    f"'{product.title}' x{ci.quantity} — {_format_ksh(line_total)}\n"
                    f"Shop: {shop.name}\n"
                    f"Buyer: {user.username}\n"
                    f"Seller: {seller.username}\n"
                    f"View: {settings.SITE_URL}/dashboard"
                )
                notified_sellers.add(shop.owner_id)

    order = Order(
        buyer_id=user.id,
        total=total,
        status=OrderStatus.PENDING,
        fulfillment_method=data.fulfillment_method,
        delivery_area=data.delivery_area,
        delivery_address=data.delivery_address,
        payment_method=data.payment_method,
        customer_phone=data.customer_phone or user.phone,
        customer_name=data.customer_name or user.username,
    )
    db.add(order)
    db.flush()

    for oid in order_items_data:
        item = OrderItem(
            order_id=order.id,
            product_id=oid["product"].id,
            price=oid["price"],
            quantity=oid["quantity"],
        )
        db.add(item)
        oid["product"].stock -= oid["quantity"]

    for ci in cart_items:
        db.delete(ci)

    db.commit()
    db.refresh(order)

    # Initiate M-Pesa payment if applicable
    payment_initiated = False
    checkout_request_id = None
    if data.payment_method == "mpesa":
        phone = data.customer_phone or user.phone
        if phone:
            clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
            if clean_phone.startswith("0"):
                clean_phone = "254" + clean_phone[1:]
            if clean_phone.startswith("254"):
                crid = _fire_mpesa_background(order.id, order.total, clean_phone)
                if crid:
                    payment_initiated = True
                    checkout_request_id = crid

    if user.phone:
        msg = f"✅ *Order #{order.id} Confirmed!*\n"
        msg += f"Total: {_format_ksh(order.total)}\n"
        if payment_initiated:
            msg += f"💰 *M-Pesa prompt sent to your phone!*\n"
            msg += f"Enter your PIN to complete payment.\n"
        msg += f"View: {settings.SITE_URL}/checkout/{order.id}"
        _notify_via_whatsapp(user.phone, msg)

    _create_order_auto_replies(db, order, user, order_items_data)

    return {
        "order_id": order.id,
        "total": order.total,
        "status": order.status.value,
        "payment_initiated": payment_initiated,
        "checkout_request_id": checkout_request_id,
        "message": "M-Pesa prompt sent to your phone!" if payment_initiated else "Order placed successfully!",
    }


@router.get("/orders/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id, Order.buyer_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    items = []
    for oi in order.items:
        if not oi.product_id:
            continue
        product = oi.product
        items.append({
            "id": oi.id,
            "type": "shop_product",
            "price": oi.price,
            "quantity": oi.quantity,
            "title": product.title if product else "Unknown",
            "image_url": product.image_url if product else None,
        })
    
    return {
        "id": order.id,
        "total": order.total,
        "status": order.status.value if order.status else "PENDING",
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "fulfillment_method": order.fulfillment_method,
        "delivery_area": order.delivery_area,
        "delivery_address": order.delivery_address,
        "delivery_fee": order.delivery_fee,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "customer_phone": order.customer_phone,
        "customer_name": order.customer_name,
        "seller_notes": order.seller_notes,
        "items": items,
    }


@router.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    orders = db.query(Order).filter(Order.buyer_id == user.id).order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        items = []
        for oi in o.items:
            if not oi.product_id:
                continue
            product = oi.product
            items.append({
                "id": oi.id,
                "type": "shop_product",
                "price": oi.price,
                "quantity": oi.quantity,
                "title": product.title if product else "Unknown",
                "image_url": product.image_url if product else None,
            })
        result.append({
            "id": o.id,
            "total": o.total,
            "status": o.status.value if o.status else "PENDING",
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "fulfillment_method": o.fulfillment_method,
            "delivery_area": o.delivery_area,
            "delivery_address": o.delivery_address,
            "delivery_fee": o.delivery_fee,
            "payment_method": o.payment_method,
            "payment_status": o.payment_status,
            "customer_phone": o.customer_phone,
            "customer_name": o.customer_name,
            "seller_notes": o.seller_notes,
            "items": items,
        })
    return result


# ---------- Order status updates ----------


VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PAID, OrderStatus.DISPATCHED, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.DISPATCHED, OrderStatus.CANCELLED],
    OrderStatus.DISPATCHED: [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update order status (seller only). Validates transition."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_seller = _is_seller_for_order(db, order, user.id)
    if not is_seller and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the seller can update order status")

    new_status = data.status.upper()
    try:
        new_enum = OrderStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

    current_enum = OrderStatus(order.status.value) if isinstance(order.status, OrderStatus) else OrderStatus(order.status)

    allowed = VALID_TRANSITIONS.get(current_enum, [])
    if new_enum not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {current_enum.value} to {new_enum.value}. Allowed: {[s.value for s in allowed] or ['none']}"
        )

    order.status = new_enum
    if data.seller_notes:
        order.seller_notes = data.seller_notes
    db.commit()

    status_labels = {
        "CONFIRMED": "✅ Order Confirmed",
        "PAID": "💰 Payment Received",
        "DISPATCHED": "🚚 Order Dispatched",
        "SHIPPED": "📦 Order Shipped",
        "DELIVERED": "📬 Order Delivered",
        "CANCELLED": "❌ Order Cancelled",
    }
    status_emoji = {
        "CONFIRMED": "✅",
        "PAID": "💰",
        "DISPATCHED": "🚚",
        "SHIPPED": "📦",
        "DELIVERED": "📬",
        "CANCELLED": "❌",
    }

    buyer_msg = (
        f"{status_emoji.get(new_enum.value, '📋')} Order #{order.id} Update\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Status: {status_labels.get(new_enum.value, new_enum.value)}\n"
    )
    if data.seller_notes:
        buyer_msg += f"Seller says: \"{data.seller_notes}\"\n"
    buyer_msg += f"━━━━━━━━━━━━━━━━━━━\n"
    buyer_msg += f"View details: {settings.SITE_URL}/checkout/{order.id}"

    buyer = db.query(User).filter(User.id == order.buyer_id).first()
    if buyer and buyer.phone:
        try:
            send_text_message_sync(
                buyer.phone,
                buyer_msg
            )
        except Exception:
            logger.warning(f"Failed to send status update to buyer {buyer.phone}")

    if buyer:
        seller_user = user
        db.add(Message(
            order_id=order.id,
            sender_id=seller_user.id,
            content=buyer_msg,
            is_auto_reply=True,
        ))
        db.commit()

    return OrderStatusUpdateResponse(
        order_id=order.id,
        status=new_enum.value,
        message=f"Order #{order.id} status updated to {new_enum.value}",
    )


def _is_seller_for_order(db: Session, order: Order, user_id: int) -> bool:
    """Check if user is a seller for any item in the order."""
    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop and product.shop.owner_id == user_id:
                return True
    return False


# ---------- Customer cancellation ----------


CANCELLABLE_STATUSES = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PAID]


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cancel an order as the buyer (within cancellation window)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.buyer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You can only cancel your own orders")

    current_enum = OrderStatus(order.status.value) if isinstance(order.status, OrderStatus) else OrderStatus(order.status)
    if current_enum not in CANCELLABLE_STATUSES:
        allowed_names = [s.value for s in CANCELLABLE_STATUSES]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order in '{current_enum.value}' status. Only cancellable when: {', '.join(allowed_names)}",
        )

    order.status = OrderStatus.CANCELLED
    db.commit()

    # Notify seller via WhatsApp
    seller_phones = set()
    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop and product.shop.owner_id:
                seller = db.query(User).filter(User.id == product.shop.owner_id).first()
                if seller and seller.phone:
                    seller_phones.add(seller.phone)

    cancel_msg = (
        f"❌ Order #{order.id} Cancelled by Customer\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Customer: {user.username} ({user.phone or 'N/A'})\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Please check your dashboard for details."
    )
    for phone in seller_phones:
        _notify_via_whatsapp(phone, cancel_msg)

    # Also add auto-reply messages
    buyer = user
    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop:
                seller_user = db.query(User).filter(User.id == product.shop.owner_id).first()
                if seller_user:
                    db.add(Message(
                        order_id=order.id, sender_id=buyer.id,
                        content=f"Order #{order.id} has been cancelled by the customer.",
                        is_auto_reply=True,
                    ))
                    break

    db.commit()

    return {
        "order_id": order.id,
        "status": "CANCELLED",
        "message": f"Order #{order.id} has been cancelled.",
    }


# ---------- Seller order management ----------


@router.get("/seller/shop-orders")
def get_seller_shop_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shops = db.query(Shop).filter(Shop.owner_id == user.id).all()
    shop_product_ids = []
    for s in shops:
        shop_product_ids.extend([p.id for p in s.products])
    items = db.query(OrderItem).filter(OrderItem.product_id.in_(shop_product_ids)).all() if shop_product_ids else []
    order_ids = list(set(oi.order_id for oi in items))
    orders = db.query(Order).filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all() if order_ids else []

    result = []
    for o in orders:
        order_items = [oi for oi in items if oi.order_id == o.id]
        result.append({
            "order_id": o.id,
            "buyer_id": o.buyer_id,
            "total": o.total,
            "status": o.status.value if o.status else "PENDING",
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "fulfillment_method": o.fulfillment_method,
            "delivery_area": o.delivery_area,
            "delivery_fee": o.delivery_fee,
            "delivery_address": o.delivery_address,
            "payment_method": o.payment_method,
            "payment_status": o.payment_status,
            "customer_name": o.customer_name,
            "customer_phone": o.customer_phone,
            "seller_notes": o.seller_notes,
            "items": [{
                "product_id": oi.product_id,
                "title": oi.product.title if oi.product else "Unknown",
                "price": oi.price,
                "quantity": oi.quantity,
            } for oi in order_items],
        })
    return result


def _create_order_auto_replies(db: Session, order: Order, buyer: User, items_data: list):
    """Generate auto-reply messages when an order is placed."""
    shop_name = None
    seller = None
    item_details = []

    for oid in items_data:
        if oid["type"] == "product":
            product = oid["product"]
            if product and product.shop:
                shop_name = product.shop.name
                seller = db.query(User).filter(User.id == product.shop.owner_id).first()
                item_details.append(f"{product.title} x{oid['quantity']}")

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

        seller_msg = Message(
            order_id=order.id,
            sender_id=buyer.id,
            content=(
                f"New Order #{order.id} from {buyer.username}!\n"
                f"Items: {items_str}\n"
                f"Total: {_format_ksh(order.total)}\n"
                f"Buyer contact: {buyer.phone or 'N/A'}\n"
                f"Please prepare the order for shipping."
            ),
            is_auto_reply=True,
        )
        db.add(seller_msg)

        if seller.phone:
            _notify_via_whatsapp(
                seller.phone,
                f"📦 New Order #{order.id}!\n"
                f"From: {buyer.username}\n"
                f"Items: {items_str}\n"
                f"Total: {_format_ksh(order.total)}\n"
                f"Check your dashboard: {settings.SITE_URL}/dashboard"
            )

    db.commit()


def _fire_mpesa_background(order_id: int, amount: float, phone: str) -> str | None:
    """Fire-and-forget M-Pesa STK Push. Returns checkout_request_id if initiated."""
    import threading
    from services.daraja import stk_push

    crid_holder = {}

    def _do_push():
        import asyncio
        from core.database import SessionLocal
        from services.daraja import stk_push
        from models import Payment, PaymentStatus

        session = SessionLocal()
        try:
            resp = asyncio.run(stk_push(
                phone=phone,
                amount=amount,
                account_ref=f"IKO{order_id}",
                transaction_desc=f"Ikobiz Order {order_id}",
            ))
            result_code = resp.get("ResponseCode")
            payment = Payment(
                order_id=order_id,
                amount=amount,
                phone=phone,
                checkout_request_id=resp.get("CheckoutRequestID"),
                merchant_request_id=resp.get("MerchantRequestID"),
                status=PaymentStatus.PENDING.value if result_code == "0" else PaymentStatus.FAILED.value,
            )
            session.add(payment)
            session.commit()
            if result_code != "0":
                send_text_message_sync(
                    phone,
                    f"⚠️ M-Pesa payment failed for Order #{order_id}. "
                    f"Please try again: {settings.SITE_URL}/checkout/{order_id}",
                )
        except Exception as e:
            logger.error(f"M-Pesa background push failed for order #{order_id}: {e}")
        finally:
            session.close()

    try:
        import asyncio
        resp = asyncio.run(stk_push(
            phone=phone,
            amount=amount,
            account_ref=f"IKO{order_id}",
            transaction_desc=f"Ikobiz Order {order_id}",
        ))
        result_code = resp.get("ResponseCode")
        crid = resp.get("CheckoutRequestID")
        if result_code == "0" and crid:
            payment = Payment(
                order_id=order_id,
                amount=amount,
                phone=phone,
                checkout_request_id=crid,
                merchant_request_id=resp.get("MerchantRequestID"),
                status=PaymentStatus.PENDING.value,
            )
            # Use same db session (will be committed by caller)
            from core.database import SessionLocal
            psession = SessionLocal()
            try:
                psession.add(payment)
                psession.commit()
            finally:
                psession.close()
            return crid
    except Exception as e:
        logger.error(f"M-Pesa push failed for order #{order_id}: {e}")
    return None


def _format_ksh(price: float) -> str:
    return "KSh " + f"{price:,.0f}"
