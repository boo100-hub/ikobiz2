"""
routes.py - WhatsApp Cloud API webhook endpoints.

GET  /webhook  — Verification challenge (used by Meta to verify your webhook).
POST /webhook  — Receive inbound messages and reply with context-aware
                 responses powered by the actual shop and product database.
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from core.database import get_db
from app.config import whatsapp_settings
from app.whatsapp.utils import extract_message
from app.whatsapp.service import send_text_message
from app.whatsapp.handler import get_reply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


# ------------------------------------------------------------------
# GET /webhook  —  Meta webhook verification
# ------------------------------------------------------------------


@router.get("")
async def verify_webhook(request: Request):
    """
    Handle the verification request from Meta.

    Expected query parameters:
      hub.mode         = "subscribe"
      hub.verify_token = <your verify token>
      hub.challenge    = <random challenge string>

    If the verify token matches, return the challenge as a plain-text
    response. Otherwise return 403.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Webhook verification: mode={mode}, token={token}")

    if mode == "subscribe" and token == whatsapp_settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(challenge)
    else:
        logger.warning("Webhook verification failed — token mismatch")
        return JSONResponse(
            status_code=403, content={"error": "Verification failed"}
        )


# ------------------------------------------------------------------
# POST /webhook  —  Inbound message handler
# ------------------------------------------------------------------


@router.post("")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive an incoming WhatsApp message, parse it, look up real shops
    and products from the database, and reply with contextual information.
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request body as JSON: {e}")
        return JSONResponse(status_code=400, content={"status": "invalid_json"})

    logger.debug(f"Webhook payload received")

    parsed = extract_message(body)
    if parsed is None:
        return {"status": "ok"}

    sender = parsed["from"]
    text = parsed["text"]

    logger.info(f"Message from {sender}: {text}")

    # Generate contextual reply from the handler
    reply = await get_reply(text, sender, db)

    # Send the reply via WhatsApp
    sent = await send_text_message(sender, reply)
    if sent:
        logger.info(f"Reply sent to {sender}")
    else:
        logger.warning(f"Failed to send reply to {sender}")

    return {"status": "ok"}
