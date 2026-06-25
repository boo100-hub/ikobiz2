"""
whatsapp_service.py - WhatsApp marketing and discovery layer.

Provides formatted messages and shop URLs that can be shared
via WhatsApp or any messaging platform.

This is a read-only channel — no sensitive operations exposed.
"""

from typing import Any


def get_base_url() -> str:
    """
    Root URL used to generate shareable shop links.
    """
    from core.config import settings
    return settings.SITE_URL


def generate_shop_url(slug: str) -> str:
    """Build a full shop URL from its slug."""
    return f"{get_base_url()}/ecobid/{slug}"


def format_shop_list_message(shops: list[dict[str, Any]]) -> str:
    """
    Build a WhatsApp-friendly plain-text message listing all shops.

    Each shop includes an emoji indicator, the name, a short description,
    and a clickable link.
    """
    if not shops:
        return "No shops available on Ikobiz yet."

    lines = [
        "🏪 *IKOBIZ SHOPS AVAILABLE*",
        "",
    ]

    for i, shop in enumerate(shops, start=1):
        name = shop.get("name", "Unknown")
        desc = shop.get("description", "")
        slug = shop.get("slug", "")
        url = generate_shop_url(slug) if slug else ""

        # Truncate long descriptions for WhatsApp readability
        short_desc = (desc[:80] + "…") if len(desc) > 80 else desc

        lines.append(f"{i}. *{name}*")
        if short_desc:
            lines.append(f"   {short_desc}")
        if url:
            lines.append(f"   👉 {url}")
        lines.append("")

    lines.append("Reply with a shop name to continue browsing.")
    return "\n".join(lines)


def build_whatsapp_response(shops: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Return both a formatted text message and a structured shop list.

    The 'message' field is ready to copy-paste into WhatsApp.
    The 'shops' array can be used by bots or future integrations.
    """
    return {
        "message": format_shop_list_message(shops),
        "shops": [
            {
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "slug": s.get("slug", ""),
                "url": generate_shop_url(s.get("slug", "")),
            }
            for s in shops
        ],
    }


def build_webhook_placeholder() -> dict[str, str]:
    """
    Placeholder for future WhatsApp Cloud API webhook.

    Returns a message indicating the webhook is ready but
    not yet connected to a real WhatsApp Business account.
    """
    return {
        "status": "webhook_ready",
        "message": "WhatsApp webhook endpoint is configured. "
                   "Connect to WhatsApp Business API to enable live messaging.",
    }
