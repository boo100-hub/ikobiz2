import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from core.config import settings
from core.database import get_db
from dependencies.auth import get_current_user
from models import User, IkobizListing, IkobizListingStatus, Product, ProductStatus, CartItem, Order, OrderItem, OrderStatus
from app.whatsapp.service import send_text_message_sync

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cart"])


class CartAddRequest(BaseModel):
    listing_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: int = 1


class CheckoutRequest(BaseModel):
    pass





# ---------- Cart ----------


@router.get("/cart")
def get_cart(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    result = []
    for ci in items:
        entry = {
            "id": ci.id,
            "quantity": ci.quantity,
            "added_at": ci.added_at.isoformat() if ci.added_at else None,
            "type": None,
            "listing": None,
            "product": None,
        }
        if ci.listing_id:
            listing = ci.listing
            entry["listing_id"] = ci.listing_id
            entry["type"] = "secondary_market"
            entry["listing"] = {
                "id": listing.id,
                "title": listing.title,
                "buy_now_price": listing.buy_now_price,
                "starting_price": listing.starting_price,
                "image_url": listing.image_url,
                "seller_name": listing.seller_name,
                "status": listing.status.value if listing.status else "OPEN",
            } if listing else None
        if ci.product_id:
            product = ci.product
            entry["product_id"] = ci.product_id
            entry["type"] = "shop_product"
            entry["product"] = {
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "image_url": product.image_url,
                "shop_name": product.shop.name if product.shop else None,
                "shop_slug": product.shop.slug if product.shop else None,
                "status": product.status.value if product.status else "active",
            } if product else None
        result.append(entry)
    return result


@router.post("/cart/add")
def add_to_cart(
    data: CartAddRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.listing_id:
        return _add_listing_to_cart(data, db, user)
    if data.product_id:
        return _add_product_to_cart(data, db, user)
    raise HTTPException(status_code=400, detail="Provide listing_id or product_id")


def _add_listing_to_cart(data: CartAddRequest, db: Session, user: User):
    listing = db.query(IkobizListing).filter(IkobizListing.id == data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status in (IkobizListingStatus.SOLD, IkobizListingStatus.CLOSED):
        raise HTTPException(status_code=400, detail="This listing is no longer available")
    if not listing.buy_now_price:
        raise HTTPException(status_code=400, detail="This listing does not have a buy-now price")
    if listing.quantity < data.quantity:
        raise HTTPException(status_code=400, detail=f"Only {listing.quantity} available")

    existing = db.query(CartItem).filter(
        CartItem.user_id == user.id,
        CartItem.listing_id == data.listing_id,
        CartItem.product_id.is_(None),
    ).first()
    if existing:
        existing.quantity += data.quantity
        db.commit()
        db.refresh(existing)
        return existing

    item = CartItem(user_id=user.id, listing_id=data.listing_id, quantity=data.quantity)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _add_product_to_cart(data: CartAddRequest, db: Session, user: User):
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
        CartItem.listing_id.is_(None),
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
def remove_cart_item(
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
        if ci.listing_id:
            listing = ci.listing
            if not listing or listing.status in (IkobizListingStatus.SOLD, IkobizListingStatus.CLOSED):
                raise HTTPException(status_code=400, detail=f"'{listing.title if listing else 'Item'}' is no longer available")
            if not listing.buy_now_price:
                raise HTTPException(status_code=400, detail=f"'{listing.title}' cannot be purchased")
            if listing.quantity < ci.quantity:
                raise HTTPException(status_code=400, detail=f"Only {listing.quantity} of '{listing.title}' available")
            line_total = listing.buy_now_price * ci.quantity
            total += line_total
            order_items_data.append({
                "type": "listing",
                "listing": listing,
                "price": listing.buy_now_price,
                "quantity": ci.quantity,
            })
            if listing.seller_id and listing.seller_id not in notified_sellers:
                seller = db.query(User).filter(User.id == listing.seller_id).first()
                if seller and seller.phone:
                    _notify_via_whatsapp(
                        settings.NOTIFY_PHONE or seller.phone,
                        f"📦 New Order!\n"
                        f"'{listing.title}' x{ci.quantity} — {_format_ksh(line_total)}\n"
                        f"Buyer: {user.username}\n"
                        f"Seller: {seller.username}\n"
                        f"View: {settings.SITE_URL}/dashboard/ikobiz"
                    )
                    notified_sellers.add(listing.seller_id)

        if ci.product_id:
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
                        settings.NOTIFY_PHONE or seller.phone,
                        f"📦 New Order!\n"
                        f"'{product.title}' x{ci.quantity} — {_format_ksh(line_total)}\n"
                        f"Shop: {shop.name}\n"
                        f"Buyer: {user.username}\n"
                        f"Seller: {seller.username}\n"
                        f"View: {settings.SITE_URL}/dashboard"
                    )
                    notified_sellers.add(shop.owner_id)

    order = Order(buyer_id=user.id, total=total, status=OrderStatus.PENDING)
    db.add(order)
    db.flush()

    for oid in order_items_data:
        if oid["type"] == "listing":
            item = OrderItem(
                order_id=order.id,
                listing_id=oid["listing"].id,
                price=oid["price"],
                quantity=oid["quantity"],
            )
            db.add(item)
            oid["listing"].quantity -= oid["quantity"]
            if oid["listing"].quantity <= 0:
                oid["listing"].status = IkobizListingStatus.SOLD
        else:
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

    if user.phone:
        _notify_via_whatsapp(
            settings.NOTIFY_PHONE or user.phone,
            f"✅ Order #{order.id} Confirmed!\n"
            f"Total: {_format_ksh(order.total)}\n"
            f"View your orders: {settings.SITE_URL}/checkout/{order.id}"
        )

    return {
        "order_id": order.id,
        "total": order.total,
        "status": order.status.value,
        "message": "Order placed successfully!",
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
            entry = {"id": oi.id, "type": None, "price": oi.price, "quantity": oi.quantity, "title": "Unknown", "image_url": None}
            if oi.listing_id:
                listing = oi.listing
                entry["type"] = "secondary_market"
                entry["title"] = listing.title if listing else "Unknown"
                entry["image_url"] = listing.image_url if listing else None
            if oi.product_id:
                product = oi.product
                entry["type"] = "shop_product"
                entry["title"] = product.title if product else "Unknown"
                entry["image_url"] = product.image_url if product else None
            items.append(entry)
        result.append({
            "id": o.id,
            "total": o.total,
            "status": o.status.value if o.status else "PENDING",
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "items": items,
        })
    return result


# ---------- Seller order management ----------


@router.get("/seller/ikobiz-orders")
def get_seller_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listings = db.query(IkobizListing).filter(IkobizListing.seller_id == user.id).all()
    listing_ids = [l.id for l in listings]
    items = db.query(OrderItem).filter(OrderItem.listing_id.in_(listing_ids)).all() if listing_ids else []
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
            "items": [{
                "listing_id": oi.listing_id,
                "title": oi.listing.title if oi.listing else "Unknown",
                "price": oi.price,
                "quantity": oi.quantity,
            } for oi in order_items],
        })
    return result


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
            "items": [{
                "product_id": oi.product_id,
                "title": oi.product.title if oi.product else "Unknown",
                "price": oi.price,
                "quantity": oi.quantity,
            } for oi in order_items],
        })
    return result


def _format_ksh(price: float) -> str:
    return "KSh " + f"{price:,.0f}"
