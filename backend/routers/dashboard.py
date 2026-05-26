"""
routers/dashboard.py - Seller dashboard summary.

GET /dashboard/summary  - returns totals for the authenticated seller
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Shop, Product, ProductStatus

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

    return {
        "total_shops": len(shops),
        "total_products": total_products,
        "active_listings": active_products,
        "low_stock_products": low_stock_products,
    }
