"""
service.py - WhatsApp Cloud API messaging service.

Provides a single async function to send text messages
via the WhatsApp Business API.
"""

import logging

import httpx

from app.config import whatsapp_settings

logger = logging.getLogger(__name__)

# ---------- Timeout ----------

HTTP_TIMEOUT = 15.0  # seconds

# ---------- Payload builder ----------


def _build_payload(to: str, message: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }


# ---------- Send text message (async) ----------


async def send_text_message(to: str, message: str) -> bool:
    """
    Send a plain text message to a WhatsApp user.

    Args:
        to:       Recipient phone number (include country code, no +).
        message:  The message body to send.

    Returns:
        True if the API accepted the request, False otherwise.
    """
    url = whatsapp_settings.GRAPH_API_URL
    headers = {
        "Authorization": f"Bearer {whatsapp_settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = _build_payload(to, message)

    if not whatsapp_settings.WHATSAPP_TOKEN or not whatsapp_settings.PHONE_NUMBER_ID:
        logger.warning(
            "WHATSAPP_TOKEN or PHONE_NUMBER_ID not set. "
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


# ---------- Send text message (sync, for non-async endpoints) ----------


def send_text_message_sync(to: str, message: str) -> bool:
    """
    Synchronous version of send_text_message for use in sync FastAPI endpoints.
    Falls back to mock log if credentials are not configured.
    """
    import httpx as sync_httpx

    url = whatsapp_settings.GRAPH_API_URL
    headers = {
        "Authorization": f"Bearer {whatsapp_settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = _build_payload(to, message)

    if not whatsapp_settings.WHATSAPP_TOKEN or not whatsapp_settings.PHONE_NUMBER_ID:
        logger.warning(
            "WHATSAPP_TOKEN or PHONE_NUMBER_ID not set. "
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
