"""
handler.py - WhatsApp message handler.

Tries AI-powered reply first (if GROQ_API_KEY is set).
Falls back to rule-based keyword matching.
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Shop, IkobizListing, IkobizListingStatus
from app.whatsapp.ai_service import get_ai_reply

logger = logging.getLogger(__name__)

SITE_URL = "http://localhost:3000"


async def get_reply(text: str, sender: str, db: Session) -> str:
    """Generate a reply — AI first, rule-based fallback."""

    reply = await get_ai_reply(text, sender)
    if reply:
        return reply

    text = text.strip().lower()

    if text in {"hi", "hello", "hey", "start", "menu", "help"}:
        return _welcome_message(db)

    if text in {"shops", "list"}:
        return _list_all_shops(db)

    if text in {"market", "secondary market", "bidding", "ikobiz"}:
        return _secondary_market_info(db)

    shops = db.query(Shop).filter(Shop.name.ilike(f"%{text}%")).all()
    if shops:
        return _format_shop_results(shops, text, db)

    products = (
        db.query(IkobizListing)
        .filter(
            IkobizListing.title.ilike(f"%{text}%"),
            IkobizListing.status.in_([IkobizListingStatus.OPEN, IkobizListingStatus.NEGOTIATING]),
        )
        .all()
    )
    if products:
        return _format_product_results(products, text)

    return _help_text()


def _welcome_message(db: Session) -> str:
    shop_count = db.query(Shop).count()
    listing_count = (
        db.query(IkobizListing)
        .filter(IkobizListing.status.in_([IkobizListingStatus.OPEN, IkobizListingStatus.NEGOTIATING]))
        .count()
    )
    return (
        "Welcome to Ikobiz Marketplace 🛍️\n\n"
        f"We have {shop_count} shop(s) and {listing_count} secondary market listing(s).\n\n"
        "▸ Send a shop name to browse their products\n"
        "▸ Send a product name to find it in the secondary market\n"
        "▸ Send \"shops\" to see all shops\n"
        "▸ Send \"market\" to explore the secondary market\n"
        "▸ Send \"help\" for all commands"
    )


def _list_all_shops(db: Session) -> str:
    shops = db.query(Shop).order_by(Shop.name).all()
    if not shops:
        return "No shops available yet. Check back soon!"
    msg = "🏪 *All Shops*\n\n"
    for s in shops:
        product_count = len(s.products) if s.products else 0
        link = f"{SITE_URL}/shops/{s.slug}"
        msg += f"*{s.name}*\n📦 {product_count} product(s)\n🔗 {link}\n\n"
    msg += "Reply with a shop name to find specific shops."
    return msg


def _format_shop_results(shops, query, db) -> str:
    msg = f"Found {len(shops)} shop(s) matching \"{query}\":\n\n"
    for s in shops:
        product_count = len(s.products) if s.products else 0
        link = f"{SITE_URL}/shops/{s.slug}"
        msg += f"🏪 *{s.name}*\n"
        if s.description:
            desc = (s.description[:80] + "…") if len(s.description) > 80 else s.description
            msg += f"   {desc}\n"
        msg += f"📦 {product_count} product(s)\n🔗 {link}\n\n"
    msg += "Tap a link to browse and add items to your cart!"
    return msg


def _format_product_results(products, query) -> str:
    msg = f"Found {len(products)} listing(s) matching \"{query}\":\n\n"
    for p in products:
        link = f"{SITE_URL}/market/{p.id}"
        msg += f"📦 *{p.title}*\n"
        msg += f"💰 Bid from {_format_ksh(p.starting_price)}"
        if p.buy_now_price:
            msg += f" or Buy Now {_format_ksh(p.buy_now_price)}"
        msg += "\n"
        msg += f"👤 Seller: {p.seller_name}\n"
        msg += f"🔗 {link}\n\n"
    msg += "Tap a link to bid, buy now, or make an offer!"
    return msg


def _secondary_market_info(db: Session) -> str:
    count = (
        db.query(IkobizListing)
        .filter(IkobizListing.status.in_([IkobizListingStatus.OPEN, IkobizListingStatus.NEGOTIATING]))
        .count()
    )
    return (
        "&#128176; *Secondary Market*\n\n"
        f"There are {count} active listing(s) available for negotiation or instant purchase.\n\n"
        "▸ Send a product name to search\n"
        "▸ Browse all listings here:\n"
        f"{SITE_URL}/market"
    )


def _help_text() -> str:
    return (
        "Ikobiz Marketplace 🤖\n\n"
        "▸ \"hi\" / \"start\" — Welcome message\n"
        "▸ \"shops\" — List all shops\n"
        "▸ \"market\" — Secondary market info\n"
        "▸ *Shop name* — Find a specific shop\n"
        "▸ *Product name* — Search secondary market\n"
        "▸ \"help\" — Show this message\n\n"
        "Visit our website:\n"
        f"{SITE_URL}"
    )


def _format_ksh(price: float) -> str:
    return "KSh " + f"{price:,.0f}"
