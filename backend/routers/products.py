"""
routers/products.py - Product CRUD with shop-owner validation.

GET    /shops/{shop_id}/products       - list products in a shop (public)
POST   /shops/{shop_id}/products       - add product (shop owner only)
PUT    /products/{product_id}          - update product (shop owner only)
DELETE /products/{product_id}          - delete product (shop owner only)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Shop, Product, ProductStatus
from schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(tags=["products"])


def _get_shop_or_404(shop_id: int, db: Session) -> Shop:
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


def _get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _require_shop_owner(shop: Shop, user: User):
    """Raise 403 if the user is not the shop owner (unless admin)."""
    if shop.owner_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this shop",
        )


# ---------- Public ----------


@router.get("/products")
def get_all_products(
    shop_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if shop_id:
        q = q.filter(Product.shop_id == shop_id)
    products = q.all()
    # Attach shop slug/name for convenience
    result = []
    for p in products:
        d = {
            "id": p.id,
            "shop_id": p.shop_id,
            "title": p.title,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "image_url": p.image_url,
            "status": p.status.value if p.status else "active",
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "shop_name": p.shop.name if p.shop else None,
            "shop_slug": p.shop.slug if p.shop else None,
        }
        result.append(d)
    return result


@router.get("/products/{product_id}")
def get_single_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_product_or_404(product_id, db)
    return {
        "id": product.id,
        "shop_id": product.shop_id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "image_url": product.image_url,
        "status": product.status.value if product.status else "active",
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "shop_name": product.shop.name if product.shop else None,
        "shop_slug": product.shop.slug if product.shop else None,
    }


@router.get("/shops/{shop_id}/products")
def get_shop_products(shop_id: int, db: Session = Depends(get_db)):
    _get_shop_or_404(shop_id, db)
    products = db.query(Product).filter(Product.shop_id == shop_id).all()
    result = []
    for p in products:
        d = {
            "id": p.id,
            "shop_id": p.shop_id,
            "title": p.title,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "image_url": p.image_url,
            "status": p.status.value if p.status else "active",
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "shop_name": p.shop.name if p.shop else None,
            "shop_slug": p.shop.slug if p.shop else None,
        }
        result.append(d)
    return result


# ---------- Seller product endpoints ----------


@router.get("/seller/products")
def get_seller_products(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return all products across the authenticated seller's shops."""
    shops = db.query(Shop).filter(Shop.owner_id == user.id).all()
    shop_ids = [s.id for s in shops]
    products = db.query(Product).filter(Product.shop_id.in_(shop_ids)).all() if shop_ids else []
    result = []
    for p in products:
        d = {
            "id": p.id,
            "shop_id": p.shop_id,
            "title": p.title,
            "description": p.description,
            "price": p.price,
            "stock": p.stock,
            "image_url": p.image_url,
            "status": p.status.value if p.status else "active",
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "shop_name": p.shop.name if p.shop else None,
        }
        result.append(d)
    return result


# ---------- Authenticated ----------


@router.post("/shops/{shop_id}/products", response_model=ProductOut, status_code=201)
def create_product(
    shop_id: int,
    data: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shop = _get_shop_or_404(shop_id, db)
    _require_shop_owner(shop, user)

    product = Product(
        shop_id=shop_id,
        title=data.title,
        description=data.description,
        price=data.price,
        stock=data.stock,
        image_url=data.image_url,
        status=ProductStatus(data.status) if data.status else ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = _get_product_or_404(product_id, db)
    shop = _get_shop_or_404(product.shop_id, db)
    _require_shop_owner(shop, user)

    if data.title is not None:
        product.title = data.title
    if data.description is not None:
        product.description = data.description
    if data.price is not None:
        product.price = data.price
    if data.stock is not None:
        product.stock = data.stock
    if data.image_url is not None:
        product.image_url = data.image_url
    if data.status is not None:
        product.status = ProductStatus(data.status)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = _get_product_or_404(product_id, db)
    shop = _get_shop_or_404(product.shop_id, db)
    _require_shop_owner(shop, user)

    db.delete(product)
    db.commit()
    return None
