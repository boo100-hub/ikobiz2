"""
routes.py - WhatsApp Cloud API webhook endpoints.

GET  /webhook  -- Verification challenge (used by Meta to verify your webhook).
POST /webhook  -- Receive inbound messages (text, voice, image, location)
                  and reply with context-aware responses.
"""

import logging
import time
import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from core.database import get_db
from app.config import whatsapp_settings
from app.whatsapp.utils import extract_message
from app.whatsapp.service import send_text_message, send_image_message, download_media, transcribe_audio
from app.whatsapp.handler import get_reply

SITE_LOGO_URL = "https://res.cloudinary.com/dbcgcdgum/image/upload/q_auto/f_auto/v1779889119/ChatGPT_Image_May_27_2026_04_38_12_PM_kpxcrf.png"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])

# Dedup cache: message_id -> timestamp. Clears entries older than 30s.
_seen_messages: dict[str, float] = {}


def _is_duplicate(message_id: str) -> bool:
    now = time.time()
    stale = [mid for mid, ts in _seen_messages.items() if now - ts > 30]
    for mid in stale:
        _seen_messages.pop(mid, None)
    if message_id in _seen_messages:
        return True
    _seen_messages[message_id] = now
    return False


@router.get("")
async def verify_webhook(request: Request):
    """Handle the verification request from Meta."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Webhook verification: mode={mode}, token={token}")

    if mode == "subscribe" and token == whatsapp_settings.VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(challenge)
    else:
        logger.warning("Webhook verification failed -- token mismatch")
        return JSONResponse(
            status_code=403, content={"error": "Verification failed"}
        )


@router.post("")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive an incoming WhatsApp message, parse it, look up real shops
    and products from the database, and reply with contextual information."""
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
    text = parsed.get("text", "") or parsed.get("raw_text", "")
    message_id = parsed.get("message_id", "")
    msg_type = parsed.get("type", "text")

    # Dedup: Meta sometimes delivers the same webhook event multiple times
    if message_id and _is_duplicate(message_id):
        logger.debug(f"Dropped duplicate message {message_id}")
        return {"status": "ok"}

    logger.info(f"Message from {sender}: type={msg_type} text={text[:80] if text else '(empty)'}")

    # Handle non-text message types
    if msg_type == "voice":
        media_id = parsed.get("media_id", "")
        mime_type = parsed.get("mime_type", "audio/ogg")
        audio_bytes = await download_media(media_id)
        if audio_bytes:
            transcribed = await transcribe_audio(audio_bytes, mime_type)
            if transcribed:
                text = transcribed
                await send_text_message(
                    sender,
                    f"🎤 I heard: \"{transcribed}\"\n\nLet me help you with that!",
                )
            else:
                text = ""
                await send_text_message(
                    sender,
                    "🎤 I received your voice note but couldn't transcribe it. "
                    "Please try sending a text message or speak clearly.",
                )
        else:
            await send_text_message(
                sender,
                "Sorry, I couldn't download your voice note. Please try again.",
            )
            return {"status": "ok"}

    elif msg_type == "image":
        media_id = parsed.get("media_id", "")
        image_bytes = await download_media(media_id)
        if image_bytes:
            # Store image temporarily and let AI describe it
            temp_dir = "/tmp/ikobiz_images"
            os.makedirs(temp_dir, exist_ok=True)
            ext = "jpg"
            mime = parsed.get("mime_type", "")
            if "png" in mime:
                ext = "png"
            elif "webp" in mime:
                ext = "webp"
            elif "gif" in mime:
                ext = "gif"
            path = os.path.join(temp_dir, f"{sender.replace('+','')}_{int(time.time())}.{ext}")
            with open(path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Stored image from {sender} at {path}")
        # If there's a caption, use it as text; otherwise just process as-is
        if not text:
            text = "(sent an image)"

    elif msg_type == "location":
        lat = parsed.get("latitude")
        lng = parsed.get("longitude")
        loc_name = parsed.get("location_name", "")
        loc_addr = parsed.get("location_address", "")
        label = loc_name or loc_addr or f"{lat},{lng}"
        text = f"my location is {label} ({lat},{lng})"
        # Store the GPS in the fulfillment state later
        await send_text_message(
            sender,
            f"📍 Got your location: {label}!\n"
            f"I'll use this to help find shops and services near you.",
        )

    # Send welcome image on greetings (only once per message_id)
    welcome_keywords = {"hi", "hello", "hey", "start", "menu", "help"}
    if text.strip().lower() in welcome_keywords:
        await send_image_message(
            sender,
            SITE_LOGO_URL,
            caption="Ikobiz Platform -- Shop, Sell & Connect",
        )

    if not text:
        return {"status": "ok"}

    # Generate contextual reply from the handler
    reply, image_url, product_title = await get_reply(text, sender, db)

    # Send product image if AI requested it via [IMG:<id>]
    if image_url:
        caption = product_title or ""
        await send_image_message(sender, image_url, caption=caption)

    # Send the reply via WhatsApp
    sent = await send_text_message(sender, reply)
    if sent:
        logger.info(f"Reply sent to {sender}")
    else:
        logger.warning(f"Failed to send reply to {sender}")

    return {"status": "ok"}
