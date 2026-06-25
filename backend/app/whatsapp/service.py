"""
service.py - WhatsApp Cloud API messaging service.

Provides async and sync functions to send text/image messages,
download media, and interact with the WhatsApp Business API.
"""

import logging
from typing import BinaryIO

import httpx

from app.config import whatsapp_settings

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 15.0


def _build_payload(to: str, message: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }


def _build_image_payload(to: str, image_url: str, caption: str = "") -> dict:
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "image",
        "image": {"link": image_url},
    }
    if caption:
        payload["image"]["caption"] = caption
    return payload


async def send_image_message(to: str, image_url: str, caption: str = "") -> bool:
    url = whatsapp_settings.GRAPH_API_URL
    headers = {
        "Authorization": f"Bearer {whatsapp_settings.META_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = _build_image_payload(to, image_url, caption)

    if not whatsapp_settings.META_TOKEN or not whatsapp_settings.PHONE_NUMBER_ID:
        logger.warning(
            "IKOBIZ_META_DEV_TOKEN or PHONE_NUMBER_ID not set. "
            "Skipping image send."
        )
        logger.info(f"[MOCK IMAGE] To: {to} | Image: {image_url}")
        return True

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Image sent to {to} — response {response.status_code}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(
                f"WhatsApp image API error {e.response.status_code}: {e.response.text}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error sending WhatsApp image: {e}")
            return False


def send_image_message_sync(to: str, image_url: str, caption: str = "") -> bool:
    import httpx as sync_httpx

    url = whatsapp_settings.GRAPH_API_URL
    headers = {
        "Authorization": f"Bearer {whatsapp_settings.META_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = _build_image_payload(to, image_url, caption)

    if not whatsapp_settings.META_TOKEN or not whatsapp_settings.PHONE_NUMBER_ID:
        logger.warning(
            "IKOBIZ_META_DEV_TOKEN or PHONE_NUMBER_ID not set. "
            "Skipping image send."
        )
        logger.info(f"[MOCK IMAGE] To: {to} | Image: {image_url}")
        return True

    try:
        with sync_httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Image sent to {to} — response {response.status_code}")
            return True
    except sync_httpx.HTTPStatusError as e:
        logger.error(f"WhatsApp image API error {e.response.status_code}: {e.response.text}")
        return False
    except sync_httpx.RequestError as e:
        logger.error(f"Network error sending WhatsApp image: {e}")
        return False


async def send_text_message(to: str, message: str) -> bool:
    url = whatsapp_settings.GRAPH_API_URL
    headers = {
        "Authorization": f"Bearer {whatsapp_settings.META_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = _build_payload(to, message)

    if not whatsapp_settings.META_TOKEN or not whatsapp_settings.PHONE_NUMBER_ID:
        logger.warning(
            "IKOBIZ_META_DEV_TOKEN or PHONE_NUMBER_ID not set. "
            "Skipping send. Install ngrok and configure env."
        )
        logger.info(f"[MOCK SEND] To: {to} | Message: {message[:60]}...")
        return True

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent to {to} — response {response.status_code}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(
                f"WhatsApp API error {e.response.status_code}: {e.response.text}"
            )
            return False
        except httpx.RequestError as e:
            logger.error(f"Network error sending WhatsApp message: {e}")
            return False


async def download_media(media_id: str) -> bytes | None:
    """Download media (voice/image) from WhatsApp servers by media ID."""
    if not whatsapp_settings.META_TOKEN:
        logger.warning("META_TOKEN not set, cannot download media")
        return None

    # Step 1: Get media URL
    media_url = f"https://graph.facebook.com/{whatsapp_settings.API_VERSION}/{media_id}"
    headers = {"Authorization": f"Bearer {whatsapp_settings.META_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(media_url, headers=headers)
            r.raise_for_status()
            data = r.json()
            url = data.get("url")
            if not url:
                logger.error(f"No URL in media response for {media_id}")
                return None

            # Step 2: Download the actual media bytes
            r2 = await client.get(url, headers=headers)
            r2.raise_for_status()
            logger.info(f"Downloaded media {media_id} ({len(r2.content)} bytes)")
            return r2.content
    except Exception as e:
        logger.error(f"Failed to download media {media_id}: {e}")
        return None


async def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> str | None:
    """Transcribe audio bytes using Groq Whisper API."""
    groq_key = whatsapp_settings.GROQ_API_KEY
    if not groq_key:
        logger.warning("GROQ_API_KEY not set, cannot transcribe audio")
        return None

    try:
        import httpx as sync_httpx

        with sync_httpx.Client(timeout=30.0) as client:
            ext = "ogg" if "ogg" in mime_type else "mp3" if "mp3" in mime_type else "m4a"
            files = {"file": (f"audio.{ext}", audio_bytes, mime_type)}
            data = {"model": "whisper-large-v3-turbo", "language": "sw", "response_format": "json"}
            headers = {"Authorization": f"Bearer {groq_key}"}
            r = client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
            r.raise_for_status()
            result = r.json()
            text = result.get("text", "").strip()
            if text:
                logger.info(f"Transcribed audio ({len(text)} chars): {text[:100]}")
                return text
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")

    return None


def send_text_message_sync(to: str, message: str) -> bool:
    import httpx as sync_httpx

    url = whatsapp_settings.GRAPH_API_URL
    headers = {
        "Authorization": f"Bearer {whatsapp_settings.META_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = _build_payload(to, message)

    if not whatsapp_settings.META_TOKEN or not whatsapp_settings.PHONE_NUMBER_ID:
        logger.warning(
            "IKOBIZ_META_DEV_TOKEN or PHONE_NUMBER_ID not set. "
            "Skipping send. Install ngrok and configure env."
        )
        logger.info(f"[MOCK SEND] To: {to} | Message: {message[:60]}...")
        return True

    try:
        with sync_httpx.Client(timeout=HTTP_TIMEOUT) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent to {to} — response {response.status_code}")
            return True
    except sync_httpx.HTTPStatusError as e:
        logger.error(f"WhatsApp API error {e.response.status_code}: {e.response.text}")
        return False
    except sync_httpx.RequestError as e:
        logger.error(f"Network error sending WhatsApp message: {e}")
        return False
