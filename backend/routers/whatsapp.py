"""
routers/whatsapp.py - WhatsApp discovery channel routes.

GET  /whatsapp/shops     - formatted shop list (public)
POST /whatsapp/webhook   - placeholder for future WhatsApp Cloud API
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
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

@router.get("/whatsapp/webhook")
def whatsapp_webhook_verify(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verify webhook with Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.VERIFY_TOKEN:
        return hub_challenge
    return {"error": "Invalid verification token"}


@router.post("/whatsapp/webhook")
def whatsapp_webhook_placeholder():
    return build_webhook_placeholder()


@router.get("/whatsapp/info")
def whatsapp_bot_info():
    """Return public bot info for WhatsApp deep linking from the frontend."""
    from app.config import whatsapp_settings
    return {
        "bot_phone": whatsapp_settings.BOT_PHONE,
        "platform_name": "Ikobiz",
        "site_url": settings.SITE_URL,
    }
