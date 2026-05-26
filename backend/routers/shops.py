"""
routers/shops.py - Shop management routes with owner-based access control.

GET    /shops                      - list all shops (public)
GET    /shops/{shop_id}            - get one shop (public)
GET    /ecobid/{slug}              - get shop by slug (public)
POST   /shops                      - create a shop (authenticated)
PUT    /shops/{shop_id}            - update own shop (owner only)
DELETE /shops/{shop_id}            - delete own shop (owner only)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Shop
from schemas.shop import ShopCreate, ShopUpdate, ShopOut

router = APIRouter(tags=["shops"])


def slugify(name: str) -> str:
    """Convert a shop name into a URL-friendly slug."""
    return name.lower().strip().replace(" ", "-").replace("_", "-")


# ---------- Public routes ----------


@router.get("/shops")
def get_all_shops(db: Session = Depends(get_db)):
    shops = db.query(Shop).all()
    return shops


@router.get("/shops/{shop_id}")
def get_single_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/ecobid/{slug}")
def get_shop_by_slug(slug: str, db: Session = Depends(get_db)):
    shop = db.query(Shop).filter(Shop.slug == slug).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


# ---------- Seller's own shops ----------


@router.get("/seller/shops")
def get_seller_shops(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the authenticated user's own shops."""
    shops = db.query(Shop).filter(Shop.owner_id == user.id).all()
    return shops


# ---------- Authenticated routes ----------


@router.post("/shops", response_model=ShopOut, status_code=201)
def create_shop(
    data: ShopCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new shop. Upgrades the user's role to seller if needed."""
    if user.role == "buyer":
        user.role = "seller"
        db.flush()
    base_slug = slugify(data.name)
    slug = base_slug
    counter = 1
    while db.query(Shop).filter(Shop.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    shop = Shop(
        owner_id=user.id,
        name=data.name,
        slug=slug,
        description=data.description,
        banner_image=data.banner_image,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


@router.put("/shops/{shop_id}", response_model=ShopOut)
def update_shop(
    shop_id: int,
    data: ShopUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a shop (owner or admin only)."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not own this shop")

    if data.name is not None:
        shop.name = data.name
        shop.slug = slugify(data.name)
    if data.description is not None:
        shop.description = data.description
    if data.banner_image is not None:
        shop.banner_image = data.banner_image

    db.commit()
    db.refresh(shop)
    return shop


@router.delete("/shops/{shop_id}", status_code=204)
def delete_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a shop (owner or admin only)."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="You do not own this shop")

    db.delete(shop)
    db.commit()
    return None
