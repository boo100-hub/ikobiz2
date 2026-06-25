"""
routers/dashboard.py - Seller dashboard summary.

GET /dashboard/summary  - returns totals for the authenticated seller
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Shop, Product, ProductStatus, Order, OrderItem, OrderStatus

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return a summary of the authenticated seller's shops and products."""

    shops = db.query(Shop).filter(Shop.owner_id == user.id).all()
    shop_ids = [s.id for s in shops]

    total_products = (
        db.query(Product).filter(Product.shop_id.in_(shop_ids)).count()
        if shop_ids
        else 0
    )

    active_products = (
        db.query(Product)
        .filter(Product.shop_id.in_(shop_ids), Product.status == ProductStatus.ACTIVE)
        .count()
        if shop_ids
        else 0
    )

    low_stock_products = (
        db.query(Product)
        .filter(Product.shop_id.in_(shop_ids), Product.stock > 0, Product.stock <= 5)
        .count()
        if shop_ids
        else 0
    )

    # get order IDs for this seller's products
    shop_product_ids = []
    for s in shops:
        shop_product_ids.extend([p.id for p in s.products])
    items = db.query(OrderItem).filter(OrderItem.product_id.in_(shop_product_ids)).all() if shop_product_ids else []
    order_ids = list(set(oi.order_id for oi in items))

    all_order_ids = order_ids

    pending_orders = 0
    confirmed_orders = 0
    paid_orders = 0
    dispatched_orders = 0
    shipped_orders = 0
    delivered_orders = 0
    total_revenue = 0.0

    if all_order_ids:
        orders = db.query(Order).filter(Order.id.in_(all_order_ids)).all()
        for o in orders:
            s = o.status.value if isinstance(o.status, OrderStatus) else str(o.status)
            if s == OrderStatus.PENDING.value:
                pending_orders += 1
            elif s == OrderStatus.CONFIRMED.value:
                confirmed_orders += 1
            elif s == OrderStatus.PAID.value:
                paid_orders += 1
            elif s == OrderStatus.DISPATCHED.value:
                dispatched_orders += 1
            elif s == OrderStatus.SHIPPED.value:
                shipped_orders += 1
            elif s == OrderStatus.DELIVERED.value:
                delivered_orders += 1
                total_revenue += o.total

    return {
        "total_shops": len(shops),
        "total_products": total_products,
        "active_listings": active_products,
        "low_stock_products": low_stock_products,
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "paid_orders": paid_orders,
        "dispatched_orders": dispatched_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "total_revenue": total_revenue,
    }
