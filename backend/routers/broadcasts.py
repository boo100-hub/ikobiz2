"""
routers/broadcasts.py - Broadcast/opt-in management for seller communications.

GET    /broadcasts              - list broadcasts for current seller's shops
POST   /broadcasts              - create a new broadcast
POST   /broadcasts/{id}/send    - send broadcast to opted-in customers
POST   /broadcasts/opt-in       - customer opt-in to shop broadcasts
POST   /broadcasts/opt-out      - customer opt-out from shop broadcasts
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Shop, Broadcast, BroadcastStatus, BroadcastOptIn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])


@router.get("")
def list_broadcasts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List broadcasts for the current seller's shops."""
    shop_ids = [s.id for s in db.query(Shop).filter(Shop.owner_id == user.id).all()]
    broadcasts = (
        db.query(Broadcast)
        .filter(Broadcast.shop_id.in_(shop_ids))
        .order_by(Broadcast.created_at.desc())
        .all()
    )
    return broadcasts


@router.post("", status_code=201)
def create_broadcast(data: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new broadcast for a shop owned by the current user."""
    shop_id = data.get("shop_id")
    shop = db.query(Shop).filter(Shop.id == shop_id, Shop.owner_id == user.id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found or not yours")

    broadcast = Broadcast(
        shop_id=shop_id,
        title=data.get("title", ""),
        message=data.get("message", ""),
        image_url=data.get("image_url"),
        status=BroadcastStatus.DRAFT,
    )
    db.add(broadcast)
    db.commit()
    return {"message": "Broadcast created", "id": broadcast.id}


@router.post("/{broadcast_id}/send")
def send_broadcast(broadcast_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Send a broadcast to all opted-in customers for the shop."""
    broadcast = db.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")

    shop = db.query(Shop).filter(Shop.id == broadcast.shop_id).first()
    if not shop or shop.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    optins = db.query(BroadcastOptIn).filter(
        BroadcastOptIn.shop_id == broadcast.shop_id,
        BroadcastOptIn.opted_in == True,
    ).all()

    sent = 0
    for optin in optins:
        try:
            from app.whatsapp.service import send_text_message_sync
            msg = f"📢 *{broadcast.title}*\n\n{broadcast.message}"
            if broadcast.image_url:
                msg += f"\n\n{broadcast.image_url}"
            msg += "\n\n---\nReply STOP to unsubscribe"
            send_text_message_sync(optin.phone, msg)
            sent += 1
        except Exception:
            logger.warning(f"Failed to send broadcast to {optin.phone}")

    broadcast.status = BroadcastStatus.SENT
    broadcast.sent_count = sent
    broadcast.sent_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Broadcast sent to {sent} customer(s)"}


@router.post("/opt-in")
def opt_in(data: dict, db: Session = Depends(get_db)):
    """Customer opt-in to a shop's broadcasts."""
    shop_id = data.get("shop_id")
    phone = data.get("phone", "").replace("+", "").replace(" ", "")
    name = data.get("name")

    existing = db.query(BroadcastOptIn).filter(
        BroadcastOptIn.shop_id == shop_id,
        BroadcastOptIn.phone == phone,
    ).first()

    if existing:
        existing.opted_in = True
        existing.name = name or existing.name
    else:
        optin = BroadcastOptIn(shop_id=shop_id, phone=phone, name=name)
        db.add(optin)

    db.commit()
    return {"message": "Opt-in successful"}


@router.post("/opt-out")
def opt_out(data: dict, db: Session = Depends(get_db)):
    """Customer opt-out from a shop's broadcasts."""
    phone = data.get("phone", "").replace("+", "").replace(" ", "")
    shop_id = data.get("shop_id")

    existing = db.query(BroadcastOptIn).filter(
        BroadcastOptIn.shop_id == shop_id,
        BroadcastOptIn.phone == phone,
    ).first()
    if existing:
        existing.opted_in = False
        db.commit()

    return {"message": "Opt-out successful"}
