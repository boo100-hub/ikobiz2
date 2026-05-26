"""
routers/whatsapp.py - WhatsApp discovery channel routes.

GET  /whatsapp/shops     - formatted shop list (public)
POST /whatsapp/webhook   - placeholder for future WhatsApp Cloud API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from models import Shop
from services.whatsapp_service import build_whatsapp_response, build_webhook_placeholder

router = APIRouter(tags=["whatsapp"])


@router.get("/whatsapp/shops")
def whatsapp_shop_list(db: Session = Depends(get_db)):
    shops = db.query(Shop).all()
    shop_dicts = [
        {
            "name": s.name,
            "description": s.description or "",
            "slug": s.slug,
        }
        for s in shops
    ]
    return build_whatsapp_response(shop_dicts)


@router.post("/whatsapp/webhook")
def whatsapp_webhook_placeholder():
    return build_webhook_placeholder()
