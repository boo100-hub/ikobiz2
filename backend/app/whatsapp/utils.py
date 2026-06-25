"""
utils.py - Helper functions for processing WhatsApp messages.

Extracts relevant fields from the incoming webhook payload.
Supports text, voice, image, and location message types.
"""

import logging

logger = logging.getLogger(__name__)


def extract_message(body: dict) -> dict | None:
    """
    Parse the incoming WhatsApp webhook payload and extract:
      - sender phone number
      - message text or transcription
      - message type
      - media info (image, voice)
      - location info

    Returns None if the payload is invalid or unsupported.
    """
    try:
        entry = body.get("entry", [])
        if not entry:
            logger.warning("No entry in webhook payload")
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            logger.warning("No changes in webhook entry")
            return None

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        msg = messages[0]
        msg_type = msg.get("type")
        from_number = msg.get("from", "")
        message_id = msg.get("id", "")

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
            if not from_number or not text:
                logger.warning("Incomplete text message payload")
                return None
            return {
                "from": from_number,
                "text": text.strip().lower(),
                "raw_text": text.strip(),
                "message_id": message_id,
                "type": "text",
            }

        if msg_type == "voice":
            voice = msg.get("voice", {})
            media_id = voice.get("id", "")
            mime_type = voice.get("mime_type", "")
            logger.info(f"Voice message from {from_number}: media_id={media_id}")
            return {
                "from": from_number,
                "text": "",
                "raw_text": "",
                "message_id": message_id,
                "type": "voice",
                "media_id": media_id,
                "mime_type": mime_type,
            }

        if msg_type == "image":
            image = msg.get("image", {})
            media_id = image.get("id", "")
            mime_type = image.get("mime_type", "")
            caption = image.get("caption", "")
            logger.info(f"Image message from {from_number}: media_id={media_id}")
            return {
                "from": from_number,
                "text": caption.strip().lower() if caption else "",
                "raw_text": caption.strip() if caption else "",
                "message_id": message_id,
                "type": "image",
                "media_id": media_id,
                "mime_type": mime_type,
            }

        if msg_type == "location":
            loc = msg.get("location", {})
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            name = loc.get("name", "")
            address = loc.get("address", "")
            logger.info(f"Location message from {from_number}: {lat},{lng}")
            return {
                "from": from_number,
                "text": "",
                "raw_text": f"{name} {address}".strip() if name or address else "",
                "message_id": message_id,
                "type": "location",
                "latitude": lat,
                "longitude": lng,
                "location_name": name,
                "location_address": address,
            }

        logger.info(f"Ignoring unsupported message type: {msg_type}")
        return None

    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return None
