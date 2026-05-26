"""
utils.py - Helper functions for processing WhatsApp messages.

Extracts relevant fields from the incoming webhook payload.
"""

import logging

logger = logging.getLogger(__name__)


def extract_message(body: dict) -> dict | None:
    """
    Parse the incoming WhatsApp webhook payload and extract:
      - sender phone number
      - message text

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

        if msg_type != "text":
            logger.info(f"Ignoring unsupported message type: {msg_type}")
            return None

        from_number = msg.get("from", "")
        text = msg.get("text", {}).get("body", "")

        if not from_number or not text:
            logger.warning("Incomplete message payload")
            return None

        return {
            "from": from_number,
            "text": text.strip().lower(),
            "raw_text": text.strip(),
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return None
