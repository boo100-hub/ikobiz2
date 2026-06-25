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
from core.config import settings
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
        category=data.category,
        location_area=data.location_area,
        location_gps_lat=data.location_gps_lat,
        location_gps_lng=data.location_gps_lng,
        fulfillment_modes=data.fulfillment_modes,
        delivery_radius_km=data.delivery_radius_km,
        delivery_fee=data.delivery_fee,
        operating_hours=data.operating_hours,
        payment_methods=data.payment_methods,
        pickup_address=data.pickup_address,
        phone=data.phone,
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
    if data.category is not None:
        shop.category = data.category
    if data.location_area is not None:
        shop.location_area = data.location_area
    if data.location_gps_lat is not None:
        shop.location_gps_lat = data.location_gps_lat
    if data.location_gps_lng is not None:
        shop.location_gps_lng = data.location_gps_lng
    if data.fulfillment_modes is not None:
        shop.fulfillment_modes = data.fulfillment_modes
    if data.delivery_radius_km is not None:
        shop.delivery_radius_km = data.delivery_radius_km
    if data.delivery_fee is not None:
        shop.delivery_fee = data.delivery_fee
    if data.operating_hours is not None:
        shop.operating_hours = data.operating_hours
    if data.payment_methods is not None:
        shop.payment_methods = data.payment_methods
    if data.pickup_address is not None:
        shop.pickup_address = data.pickup_address
    if data.phone is not None:
        shop.phone = data.phone

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


# ---------- Shop share link ----------


@router.get("/shop/{shop_id}/share")
def get_shop_share_link(shop_id: int, db: Session = Depends(get_db)):
    """Get a shareable link for a shop (public)."""
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    whatsapp_deep_link = f"https://wa.me/?text=Check%20out%20{shop.name}%20on%20Ikobiz!%20{settings.SITE_URL}/shops/{shop.slug}"
    return {
        "shop_name": shop.name,
        "slug": shop.slug,
        "web_link": f"{settings.SITE_URL}/shops/{shop.slug}",
        "whatsapp_share_link": whatsapp_deep_link,
    }


# ---------- Set shop context for WhatsApp session ----------


@router.post("/session/set-shop-context")
def set_shop_context_session(phone: str, slug: str, db: Session = Depends(get_db)):
    """Set a shop context in the user's WhatsApp session so the AI focuses on this shop.
    
    Called from the web frontend when a user clicks 'Ask about this shop' on a shop page.
    The phone number should be the user's WhatsApp number (with country code, no +).
    """
    from models.chat import ChatSession
    import json
    shop = db.query(Shop).filter(Shop.slug == slug).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    session = db.query(ChatSession).filter(ChatSession.sender == phone).first()
    if not session:
        return {"status": "no_session", "message": "No active session. Send a message to the bot first."}
    state = {}
    if session.state:
        try:
            state = json.loads(session.state)
        except (json.JSONDecodeError, TypeError):
            state = {}
    state["shop_context"] = {"shop_id": shop.id, "shop_name": shop.name, "shop_slug": shop.slug}
    session.state = json.dumps(state)
    from datetime import datetime, timezone
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "status": "ok",
        "shop_name": shop.name,
        "message": f"Now focused on {shop.name}. Send a message via WhatsApp to ask about products!"
    }
