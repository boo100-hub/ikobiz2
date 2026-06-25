"""
handler.py - AI-first WhatsApp message handler with rule-based fallback.

The AI (Mistral/Groq) handles all conversations naturally.
Falls back to keyword matching when AI is unavailable.
AI markers [BUY:<id>], [IMG:<id>], [OFFER:<id>:amount] trigger actions.
Seller/buyer role detection provides rich context.
"""

import logging
import secrets
import re
from datetime import datetime, timezone
from collections import defaultdict
from urllib.parse import quote
from sqlalchemy.orm import Session
from core.config import settings
from models import User, Shop, Product, ProductStatus, Offer, OfferStatus, Order, OrderItem, OrderStatus, Message, ChatMessage, ChatSession, PickupPoint
from core.security import hash_password
from app.whatsapp.ai_service import get_ai_reply
from app.whatsapp.service import send_text_message_sync

logger = logging.getLogger(__name__)

# Regex to detect AI markers
_AI_BUY_MARKER = re.compile(r"\[BUY:\s*(\d+)(?::\s*(\d+))?\]", re.IGNORECASE)
_AI_IMG_MARKER = re.compile(r"\[IMG:\s*(\d+)\]", re.IGNORECASE)
_AI_OFFER_MARKER = re.compile(r"\[OFFER:\s*(\d+):\s*([\d.]+)\]", re.IGNORECASE)

# Service booking markers
_AI_BOOK_MARKER = re.compile(r"\[BOOK:\s*(\d+)\]", re.IGNORECASE)
_AI_BOOK_DATE_MARKER = re.compile(r"\[BOOK_DATE:\s*(\d+):\s*(.+?)\]", re.IGNORECASE)
_AI_BOOK_TIME_MARKER = re.compile(r"\[BOOK_TIME:\s*(\d+):\s*(.+?)\]", re.IGNORECASE)
_AI_BOOK_LOCATION_MARKER = re.compile(r"\[BOOK_LOCATION:\s*(\d+):\s*(\w+)\]", re.IGNORECASE)
_AI_BOOK_CONFIRM = re.compile(r"\[BOOK_CONFIRM:\s*(\d+)\]", re.IGNORECASE)

# AI escalation marker
_AI_ESCALATE = re.compile(r"\[ESCALATE:\s*(.+?)\]", re.IGNORECASE)

# Seller action markers (anywhere in text -- stripped before sending to user)
_AI_ADD_PRODUCT = re.compile(r"\[ADD_PRODUCT:\s*(\d+):\s*(.+?):\s*([\d.]+):\s*(\d+)\]", re.IGNORECASE)
_AI_UPDATE_STOCK = re.compile(r"\[UPDATE_STOCK:\s*(\d+):\s*(\d+)\]", re.IGNORECASE)
_AI_UPDATE_PRICE = re.compile(r"\[UPDATE_PRICE:\s*(\d+):\s*([\d.]+)\]", re.IGNORECASE)
_AI_SET_STATUS = re.compile(r"\[SET_STATUS:\s*(\d+):\s*(\w+)\]", re.IGNORECASE)
_AI_MARK_SHIPPED = re.compile(r"\[MARK_SHIPPED:\s*(\d+)\]", re.IGNORECASE)

# Buyer action markers
_AI_CANCEL_ORDER = re.compile(r"\[CANCEL_ORDER:\s*(\d+)\]", re.IGNORECASE)

# Budget marker
_AI_BUDGET_MARKER = re.compile(r"\[BUDGET:\s*([\d.]+)\]", re.IGNORECASE)

# Fulfillment flow markers (AI-driven)
_AI_FULFILL_METHOD = re.compile(r"\[METHOD:\s*(delivery|pickup)\]", re.IGNORECASE)
_AI_FULFILL_PICKUP = re.compile(r"\[PICKUP:\s*(\d+)\]", re.IGNORECASE)
_AI_FULFILL_LOCATION = re.compile(r"\[LOCATION:\s*(.+?)\]", re.IGNORECASE)
_AI_FULFILL_CONFIRM = re.compile(r"\[PLACE_ORDER\]", re.IGNORECASE)
_AI_FULFILL_CANCEL = re.compile(r"\[CANCEL_FLOW\]", re.IGNORECASE)

# ---------- In-memory pending seller actions ----------
_pending_seller_actions: dict[str, dict] = {}

# ---------- In-memory pending selections ----------
_pending_selections: dict[str, dict] = {}

# ---------- In-memory buyer budgets ----------
_buyer_budgets: dict[str, float] = {}

# ---------- In-memory pending cancellations ----------
_pending_cancellations: dict[str, list] = {}

# ---------- Seller registration flow state ----------
_pending_seller_regs: dict[str, dict] = {}

# ---------- Product addition flow state ----------
_pending_product_adds: dict[str, dict] = {}

# ---------- Booking flow state (for services) ----------
_pending_bookings: dict[str, dict] = {}

# ---------- Escalation tracking ----------
_escalated_sessions: dict[str, bool] = {}

# ---------- Swahili keyword mapping ----------
SWAHILI_KEYWORDS = {
    "kununua": "buy",
    "tafuta": "search",
    "nahitaji": "i need",
    "nisaidie": "help",
    "bei": "price",
    "ghali": "expensive",
    "rahisi": "cheap",
    "duka": "shop",
    "maduka": "shops",
    "mboga": "vegetables",
    "matunda": "fruits",
    "nguo": "clothes",
    "viatu": "shoes",
    "simu": "phone",
    "samsung": "samsung",
    "fundi": "technician",
    "mpishi": "cook",
    "mwelekezi": "tailor",
    "kinyozi": "barber",
    "karani": "clerk",
    "muuzaji": "seller",
    "orodha": "list",
    "jambo": "hi",
    "habari": "hi",
    "sijambo": "hi",
    "asante": "thanks",
    "tafadhali": "please",
    "sawa": "ok",
    "ndiyo": "yes",
    "hapana": "no",
    "sijui": "i dont know",
}


# ---------- Fulfillment flow state (file-backed for multi-worker) ----------
import json
import os

_FULFILLMENT_DIR = "/tmp/ikobiz_fulfillment"
_pending_fulfillment: dict[str, dict] = {}

def _ensure_dir():
    os.makedirs(_FULFILLMENT_DIR, exist_ok=True)

def _state_path(sender: str) -> str:
    return os.path.join(_FULFILLMENT_DIR, f"{sender}.json")

def _load_state(sender: str) -> dict | None:
    if sender in _pending_fulfillment:
        return _pending_fulfillment[sender]
    path = _state_path(sender)
    try:
        with open(path) as f:
            data = json.load(f)
            _pending_fulfillment[sender] = data
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def _save_state(sender: str, data: dict):
    _pending_fulfillment[sender] = data
    _ensure_dir()
    with open(_state_path(sender), "w") as f:
        json.dump(data, f)

def _del_state(sender: str):
    _pending_fulfillment.pop(sender, None)
    path = _state_path(sender)
    if os.path.exists(path):
        os.remove(path)

# ---------- Conversation history ----------

MAX_HISTORY = 10


def _get_conversation_history(sender: str, db: Session) -> list[dict]:
    """Fetch the last MAX_HISTORY messages for this sender."""
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.sender == sender)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def _save_conversation(sender: str, role: str, content: str, db: Session):
    msg = ChatMessage(sender=sender, role=role, content=content)
    db.add(msg)
    db.commit()


# ---------- Session management ----------


def _get_or_create_session(sender: str, db: Session) -> ChatSession:
    """Get existing session for a sender or create a new one with role detection."""
    session = db.query(ChatSession).filter(ChatSession.sender == sender).first()
    if session:
        session.updated_at = datetime.now(timezone.utc)
        session.is_active = True
        db.commit()
        return session

    user = db.query(User).filter(User.phone == sender.replace("+", "").replace(" ", "")).first()
    role = user.role if user else "buyer"
    session = ChatSession(sender=sender, user_id=user.id if user else None, role=role)
    db.add(session)
    db.commit()
    logger.info(f"Created new session for {sender} with role={role}")
    return session


def _update_session_role(session: ChatSession, new_role: str, db: Session):
    """Update the session's role (e.g., buyer -> seller)."""
    session.role = new_role
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Updated session for {session.sender} to role={new_role}")


def _sync_session_user(session: ChatSession, db: Session):
    """Sync session with current user data from DB."""
    user = db.query(User).filter(User.phone == session.sender.replace("+", "").replace(" ", "")).first()
    if user:
        session.user_id = user.id
        if user.role in ("seller", "admin") and session.role != user.role:
            session.role = user.role
            logger.info(f"Session {session.sender} synced to role={user.role}")
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
    return session


def _get_session_context(session: ChatSession) -> str | None:
    """Build a context string about the current session for the AI."""
    return (
        f"User session role: {session.role}\n"
        f"Session active: {session.is_active}\n"
        f"The user is interacting as a {'seller/store manager' if session.role in ('seller', 'admin') else 'buyer/visitor'} on the platform."
    )


# ---------- Seller detection and context ----------


def _get_seller(sender: str, db: Session) -> User | None:
    """Look up a seller by WhatsApp phone number."""
    safe = sender.replace("+", "").replace(" ", "")
    return db.query(User).filter(User.phone == safe, User.role.in_(["seller", "admin"])).first()


def _get_seller_context(seller: User, db: Session) -> str | None:
    """Fetch seller's own shops, products, and recent orders as formatted context."""
    shops = db.query(Shop).filter(Shop.owner_id == seller.id).all()
    if not shops:
        return None

    shop_ids = [s.id for s in shops]
    products = db.query(Product).filter(Product.shop_id.in_(shop_ids)).order_by(Product.title).all()
    shop_names = {s.id: s.name for s in shops}

    lines = [f"Your shops ({len(shops)}):"]
    for s in shops:
        p_count = len([p for p in products if p.shop_id == s.id])
        lines.append(f"  🏪 {s.name} (ID:{s.id}) -- {p_count} product(s)")

    if products:
        lines.append(f"\nYour products ({len(products)}):")
        for p in products:
            lines.append(
                f"  📦 ID:{p.id} | {p.title} | KSh {p.price:,.0f} | "
                f"Stock: {p.stock} | Status: {p.status.value} | Shop: {shop_names.get(p.shop_id, '?')}"
            )

    recent_orders = (
        db.query(Order)
        .join(OrderItem)
        .filter(
            OrderItem.product_id.in_([p.id for p in products]) if products else False,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED]),
        )
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )
    if recent_orders:
        lines.append(f"\nRecent orders ({len(recent_orders)}):")
        for o in recent_orders:
            buyer = db.query(User).filter(User.id == o.buyer_id).first()
            buyer_name = buyer.username if buyer else "?"
            lines.append(f"  🆔 Order #{o.id} | {buyer_name} | KSh {o.total:,.0f} | {o.status.value}")

    lines.append(f"\nShare links (you can share these with customers):")
    for s in shops:
        link = _get_shop_share_link(s)
        lines.append(f"  🔗 {s.name}: {link}")

    lines.append(f"\nTo add a product, just say \"add product\" and I'll guide you through it!")
    lines.append(f"To see your share links, say \"my shop link\".")

    return "\n".join(lines)


# ---------- Buyer detection and context ----------


def _get_buyer(sender: str, db: Session) -> User | None:
    """Look up an existing buyer by WhatsApp phone number (does NOT create)."""
    safe = sender.replace("+", "").replace(" ", "")
    return db.query(User).filter(User.phone == safe, User.role == "buyer").first()


def _get_buyer_context(buyer: User, db: Session) -> str:
    """Fetch buyer's orders with product details as formatted context."""
    orders = (
        db.query(Order)
        .filter(Order.buyer_id == buyer.id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )
    if not orders:
        return f"Your account: {buyer.username} ({buyer.phone}). You have no orders yet."

    lines = [f"Your account: {buyer.username} ({buyer.phone})"]
    lines.append(f"\nYour orders ({len(orders)}):")
    for o in orders:
        items = []
        for item in o.items:
            p = db.query(Product).filter(Product.id == item.product_id).first()
            title = p.title if p else "?"
            shop_name = p.shop.name if p and p.shop else "?"
            items.append(f"{title} (x{item.quantity}) -- {shop_name}")
        items_str = ", ".join(items) if items else "N/A"
        lines.append(f"  🆔 Order #{o.id} | KSh {o.total:,.0f} | {o.status.value} | {items_str}")

    return "\n".join(lines)


# ---------- Budget context for AI ----------


def _get_budget_context(sender: str) -> str | None:
    """Return the buyer's known budget as formatted context."""
    budget = _buyer_budgets.get(sender)
    if budget is not None:
        return f"This buyer's budget is KSh {budget:,.0f}. Recommend products within this range."
    return None


def _process_budget_marker(reply: str, sender: str) -> str:
    """Extract and store [BUDGET:<amount>] marker. Returns cleaned text."""
    m = _AI_BUDGET_MARKER.search(reply)
    if m:
        amount = float(m.group(1))
        _buyer_budgets[sender] = amount
        logger.info(f"Stored budget KSh {amount:,.0f} for {sender}")
        reply = _AI_BUDGET_MARKER.sub("", reply).strip()
    return reply


# ---------- Database context for AI ----------


def _get_db_context_data(db: Session) -> str:
    """Fetch all shops and active products as formatted text for AI context.
    Includes categories, attributes, and price ranges for smarter recommendations.
    Separates physical products from services."""
    shops = db.query(Shop).order_by(Shop.name).all()
    products = db.query(Product).filter(Product.status == "ACTIVE").order_by(Product.title).all()
    physical = [p for p in products if not _is_service(p)]
    services = [p for p in products if _is_service(p)]

    lines = ["Shops:"]
    for s in shops:
        line = f"- {s.name} (slug: {s.slug})"
        if s.description:
            line += f" -- {s.description[:120]}"
        if s.category:
            line += f" | Category: {s.category}"
        if s.location_area:
            line += f" | Location: {s.location_area}"
        if s.pickup_address:
            line += f" | Pickup: {s.pickup_address}"
        if s.phone:
            line += f" | Phone: {s.phone}"
        if s.fulfillment_modes:
            line += f" | Fulfillment: {s.fulfillment_modes}"
        lines.append(line)

    lines.append(f"\nPhysical Products (Available to buy - {len(physical)}):")
    for p in physical:
        shop_name = p.shop.name if p.shop else "Unknown"
        cat = f" | Category: {p.category}" if p.category else ""
        attrs = f" | Attributes: {p.attributes}" if p.attributes else ""
        desc = f" | {p.description[:80]}" if p.description else ""
        lines.append(
            f"- ID:{p.id} | {p.title}{desc} | KSh {p.price:,.0f} | Stock: {p.stock}{cat}{attrs} | Shop: {shop_name}"
        )

    lines.append(f"\nServices (Available to book - {len(services)}):")
    for p in services:
        shop_name = p.shop.name if p.shop else "Unknown"
        dur = f" | Duration: ~{p.service_duration_minutes}min" if p.service_duration_minutes else ""
        cat = f" | Category: {p.category}" if p.category else ""
        desc = f" | {p.description[:80]}" if p.description else ""
        lines.append(
            f"- ID:{p.id} | {p.title}{desc} | KSh {p.price:,.0f}{dur}{cat} | Shop: {shop_name}"
        )

    # Group by category with price ranges
    by_category = defaultdict(list)
    for p in products:
        cat = p.category or "Uncategorized"
        by_category[cat].append(p.price)

    lines.append("\nPrice Ranges by Category:")
    for cat, prices in sorted(by_category.items()):
        min_p = min(prices)
        max_p = max(prices)
        count = len(prices)
        lines.append(f"  {cat}: KSh {min_p:,.0f} - KSh {max_p:,.0f} ({count} product(s))")

    # Also show shops by location for hyperlocal awareness
    lines.append("\nShops by Location:")
    by_location = defaultdict(list)
    for s in shops:
        loc = s.location_area or "Unknown"
        by_location[loc].append(s.name)
    for loc, names in sorted(by_location.items()):
        lines.append(f"  {loc}: {', '.join(names)}")

    return "\n".join(lines)


# ---------- WhatsApp notification helper ----------


def _notify_via_whatsapp(phone: str | None, message: str):
    if phone:
        try:
            send_text_message_sync(phone, message)
        except Exception:
            logger.warning(f"Failed to send WhatsApp notification to {phone}")


# ---------- Fulfillment flow (AI-driven with markers) ----------


def _filter_pickup_points(points: list, shop: Shop | None) -> list:
    """Filter pickup points to those relevant to the shop's area/region."""
    if not shop or not shop.location_area:
        return points
    nairobi_areas = {"westlands", "nairobi cbd", "kilimani", "kasarani", "buruburu", "nairobi"}
    shop_area = shop.location_area.lower().strip()
    shop_in_nairobi = any(a in shop_area or shop_area in a for a in nairobi_areas)
    if shop_in_nairobi:
        return [p for p in points if p.area and any(
            na in p.area.lower() for na in nairobi_areas
        )]
    return [p for p in points if p.area and (
        p.area.lower() == shop_area or shop_area in p.area.lower() or p.area.lower() in shop_area
    )] or points


def _get_pickup_points_text(db: Session, shop: Shop | None = None) -> str | None:
    """Fetch pickup points from DB filtered by shop area and format for display."""
    points = db.query(PickupPoint).order_by(PickupPoint.area, PickupPoint.name).all()
    if not points:
        return None
    filtered = _filter_pickup_points(points, shop) if shop else points
    if not filtered:
        return None
    lines = ["📍 *Pickup Points*", "━━━━━━━━━━━━━━━━━━━"]
    for i, p in enumerate(filtered, 1):
        loc = f" ({p.area})" if p.area else ""
        lines.append(f"{i}. *{p.name}*{loc}")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


def _is_in_fulfillment_flow(sender: str) -> bool:
    state = _load_state(sender)
    return state is not None and state.get("step") is not None


def _load_items(state: dict, db: Session) -> list:
    """Re-query products from DB to avoid DetachedInstanceError."""
    raw = state.get("items", [])
    result = []
    for entry in raw:
        if isinstance(entry[0], int):
            product = db.query(Product).filter(Product.id == entry[0]).first()
            if product:
                result.append((product, entry[1]))
        else:
            result.append(entry)
    state["items"] = [(p.id, qty) for p, qty in result]
    return result


def _start_fulfillment_flow(sender: str, items: list, db: Session) -> str:
    """Begin the fulfillment conversation. Sets step to 'choose_method' so AI can guide the user."""
    state = {
        "items": [(p.id, qty) for p, qty in items],
        "step": "choose_method",
        "fulfillment_method": None,
        "pickup_point_id": None,
        "pickup_point_name": None,
        "pickup_point_area": None,
        "delivery_area": None,
    }
    _save_state(sender, state)
    loaded = _load_items(state, db)
    subtotal = sum(p.price * qty for p, qty in loaded)
    first_shop = loaded[0][0].shop if loaded else None
    store_label = first_shop.name if first_shop else "Ikobiz Platform"
    lines = [
        "🛍️ *Your Order*",
        "━━━━━━━━━━━━━━━━━━━",
    ]
    for p, qty in loaded:
        lines.append(f"• {p.title} × {qty} — KSh {p.price * qty:,.0f}")
    lines.append(f"━━━━━━━━━━━━━━━━━━━")
    lines.append(f"*Total:* KSh {subtotal:,.0f}")
    lines.append("")
    lines.append(f"🏪 {store_label}")
    lines.append("")
    lines.append("How would you like to receive your order?")
    lines.append("1️⃣ *Delivery* 📍 — I'll share my location")
    lines.append("2️⃣ *Pickup* 🏪 — I'll pick up at a point")
    return "\n".join(lines)


def _handle_fulfillment_step(sender: str, text: str, db: Session) -> str | None:
    """
    Rule-based fallback for fulfillment steps where the AI didn't use markers.
    Handles simple number selections and confirm/cancel.
    """
    state = _load_state(sender)
    if not state:
        return None
    lower = text.strip().lower()
    step = state.get("step")

    if step == "choose_method":
        if lower in ("1", "delivery"):
            state["fulfillment_method"] = "delivery"
            state["step"] = "delivery_location"
            _save_state(sender, state)
            return "📍 Great! Please share your delivery location or area (e.g., 'Westlands, Nairobi')."
        if lower in ("2", "pickup"):
            state["fulfillment_method"] = "pickup"
            state["step"] = "pickup_point"
            _save_state(sender, state)
            loaded = _load_items(state, db)
            first_product = loaded[0][0] if loaded else None
            shop = first_product.shop if first_product else None
            pickup_text = _get_pickup_points_text(db, shop)
            if pickup_text:
                return f"{pickup_text}\n\nReply with the number of your preferred pickup point."
            return "📍 Please type your preferred pickup area."

    if step == "pickup_point":
        if re.match(r"^\d{1,2}$", lower):
            idx = int(lower)
            loaded = _load_items(state, db)
            first_product = loaded[0][0] if loaded else None
            shop = first_product.shop if first_product else None
            points = db.query(PickupPoint).order_by(PickupPoint.area, PickupPoint.name).all()
            filtered = _filter_pickup_points(points, shop)
            if 1 <= idx <= len(filtered):
                pp = filtered[idx - 1]
                state["pickup_point_id"] = pp.id
                state["pickup_point_name"] = pp.name
                state["pickup_point_area"] = pp.area or ""
                state["step"] = "confirm"
                _save_state(sender, state)
                summary = _build_order_summary(state, db)
                return f"{summary}\n\nReply ✅ *confirm* to place your order, or ❌ *cancel*."
            return f"Please select a number between 1 and {len(filtered)}."

    if step == "delivery_location":
        if lower not in ("delivery", "pickup", "1", "2"):
            state["delivery_area"] = text.strip()
            state["step"] = "confirm"
            _save_state(sender, state)
            summary = _build_order_summary(state, db)
            return f"{summary}\n\nReply ✅ *confirm* to place your order, or ❌ *cancel*."

    if step == "confirm":
        if lower in ("confirm", "yes", "yeah", "ok", "okay", "yep", "sure", "place", "order"):
            reply = _finalize_fulfillment(sender, db)
            _del_state(sender)
            return reply
        if lower in ("cancel", "no", "nope", "never mind", "stop"):
            _del_state(sender)
            return "No problem! Your order has been cancelled. Let me know if you need anything else. 😊"

    return None


def _build_fulfillment_context(sender: str, db: Session) -> str | None:
    """Build AI context from the current fulfillment state so the AI can guide the user naturally."""
    state = _load_state(sender)
    if not state:
        return None
    step = state.get("step")
    items = _load_items(state, db)
    if not items:
        return None

    first_product = items[0][0]
    shop = first_product.shop

    lines = [
        "\n\n=== FULFILLMENT FLOW ===",
        f"Current step: {step}",
        "Items in cart:",
    ]
    for p, qty in items:
        sname = p.shop.name if p.shop else "Ikobiz"
        lines.append(f"  • {p.title} x{qty} @ KSh {p.price}/ea = KSh {p.price*qty} ({sname})")
    lines.append(f"Subtotal: KSh {sum(p.price*qty for p,qty in items)}")

    if step == "choose_method":
        lines.append("\nAsk user: delivery or pickup?")
        lines.append("If delivery, use marker: [METHOD:delivery]")
        lines.append("If pickup, use marker: [METHOD:pickup]")
    elif step == "delivery_location":
        lines.append("\nAsk user for their delivery area/location.")
        lines.append("When they provide it, use marker: [LOCATION:<area>]")
    elif step == "pickup_point":
        points = db.query(PickupPoint).order_by(PickupPoint.area, PickupPoint.name).all()
        filtered = _filter_pickup_points(points, shop)
        if filtered:
            lines.append("\nAvailable pickup points (show these to user):")
            for i, pp in enumerate(filtered, 1):
                loc = f" ({pp.area})" if pp.area else ""
                lines.append(f"  {i}. {pp.name}{loc}")
            lines.append("\nWhen user picks one, use: [PICKUP:<number>]")
        else:
            lines.append("\nAsk user to type their preferred pickup area.")
    elif step == "confirm":
        method = state.get("fulfillment_method", "pickup")
        loc = state.get("pickup_point_name") or state.get("delivery_area", "?")
        lines.append(f"\nFulfillment: {method.upper()} at {loc}")
        lines.append("\nShow checkout summary and ask user to confirm.")
        lines.append("To place order: [PLACE_ORDER]")
        lines.append("To cancel: [CANCEL_FLOW]")

    lines.append("\nIMPORTANT RULES:")
    lines.append("- Be conversational and friendly.")
    lines.append("- Guide the user through the steps naturally.")
    lines.append("- ONLY use the markers listed above to signal actions.")
    lines.append("- NEVER ask user to type numbers or commands.")
    return "\n".join(lines)


# ---------- Service booking flow ----------


def _is_service(product: Product) -> bool:
    """Check if a product is a service type."""
    return getattr(product, 'product_type', 'physical') == 'service'


def _is_in_booking_flow(sender: str) -> bool:
    return sender in _pending_bookings


def _start_booking_flow(sender: str, service: Product, db: Session) -> str:
    """Begin the service booking conversation."""
    shop = service.shop
    seller = db.query(User).filter(User.id == shop.owner_id).first() if shop else None

    _pending_bookings[sender] = {
        "service_id": service.id,
        "service_title": service.title,
        "shop_id": shop.id if shop else None,
        "seller_id": seller.id if seller else None,
        "price": service.price,
        "duration_minutes": service.service_duration_minutes,
        "step": "choose_date",
        "scheduled_date": None,
        "scheduled_time": None,
        "location_type": "at_seller",
        "location_address": shop.pickup_address if shop else None,
    }

    duration = ""
    if service.service_duration_minutes:
        duration = f"\n⏱️ Duration: ~{service.service_duration_minutes} minutes"

    return (
        f"📅 *Booking: {service.title}*\n"
        f"💰 KSh {service.price:,.0f}{duration}\n"
        f"🏪 {shop.name if shop else 'Ikobiz'}\n\n"
        f"What date would you like to book?\n"
        f"(e.g., 'tomorrow', 'Friday', 'December 25th', or a specific date)"
    )


def _handle_booking_step(sender: str, text: str, db: Session) -> str | None:
    """Rule-based fallback for booking flow steps."""
    booking = _pending_bookings.get(sender)
    if not booking:
        return None
    lower = text.strip().lower()
    step = booking.get("step")

    if step == "choose_date":
        booking["scheduled_date_raw"] = lower
        booking["step"] = "choose_time"
        return (
            f"Got it! 🗓️\n\n"
            f"What time would you prefer?\n"
            f"(e.g., '10am', '2:30 PM', 'morning', 'afternoon')"
        )

    if step == "choose_time":
        booking["scheduled_time_raw"] = lower
        booking["step"] = "choose_location"
        shop = db.query(Shop).filter(Shop.id == booking["shop_id"]).first() if booking.get("shop_id") else None
        lines = [
            "📍 *Location Preference*",
            "\nWhere would you like the service?",
            "\n1️⃣ *At their location* 🏪",
        ]
        if shop and shop.pickup_address:
            lines.append(f"   {shop.pickup_address}")
        lines.append("\n2️⃣ *At my location* 🏠")
        lines.append("   I'll share my address")
        lines.append("\n3️⃣ *Remote/Online* 💻")
        lines.append("   (if applicable)")
        return "\n".join(lines)

    if step == "choose_location":
        if lower in ("1", "their", "their location", "at seller", "shop"):
            booking["location_type"] = "at_seller"
            shop = db.query(Shop).filter(Shop.id == booking["shop_id"]).first() if booking.get("shop_id") else None
            booking["location_address"] = shop.pickup_address if shop else ""
            booking["step"] = "confirm"
        elif lower in ("2", "my", "my location", "home", "at buyer"):
            booking["location_type"] = "at_buyer"
            booking["step"] = "buyer_address"
            return "Please share your address or location where the service should be provided. 📍"
        elif lower in ("3", "remote", "online", "virtual"):
            booking["location_type"] = "remote"
            booking["step"] = "confirm"
        else:
            return "Please choose 1 (their location), 2 (my location), or 3 (remote)."

        return _show_booking_summary(sender, booking, db)

    if step == "buyer_address":
        booking["location_address"] = text.strip()
        booking["step"] = "confirm"
        return _show_booking_summary(sender, booking, db)

    if step == "confirm":
        if lower in ("confirm", "yes", "ndiyo", "ok", "okay", "yep", "sawa", "sure"):
            return _finalize_booking(sender, booking, db)
        if lower in ("cancel", "no", "hapana", "nope", "never mind", "stop"):
            del _pending_bookings[sender]
            return "No problem! Your booking request has been cancelled. Let me know if you need anything else! 😊"

    return None


def _show_booking_summary(sender: str, booking: dict, db: Session) -> str:
    """Build a booking summary for the user to confirm."""
    shop = db.query(Shop).filter(Shop.id == booking["shop_id"]).first() if booking.get("shop_id") else None
    loc_type_labels = {"at_seller": "At their location", "at_buyer": "At my location", "remote": "Remote/Online"}
    loc_label = loc_type_labels.get(booking["location_type"], booking["location_type"])
    addr = booking.get("location_address", "")
    addr_line = f"\n📍 {addr}" if addr else ""

    duration = ""
    if booking.get("duration_minutes"):
        duration = f"\n⏱️ Duration: ~{booking['duration_minutes']} minutes"

    return (
        f"📋 *Booking Summary*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *{booking['service_title']}*\n"
        f"💰 KSh {booking['price']:,.0f}{duration}\n"
        f"🗓️ Date: {booking.get('scheduled_date_raw', 'TBD')}\n"
        f"⏰ Time: {booking.get('scheduled_time_raw', 'TBD')}\n"
        f"📍 {loc_label}{addr_line}\n"
        f"🏪 {shop.name if shop else 'Ikobiz'}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Reply ✅ *confirm* to book, or ❌ *cancel* to discard."
    )


def _finalize_booking(sender: str, booking: dict, db: Session) -> str:
    """Create the Booking record and notify the seller."""
    from datetime import date, time
    from models import Booking, BookingStatus

    buyer = _find_or_create_buyer(db, sender)
    seller_id = booking.get("seller_id")
    shop_id = booking.get("shop_id")

    now = date.today()

    booking_record = Booking(
        service_id=booking["service_id"],
        buyer_id=buyer.id,
        seller_id=seller_id or 0,
        shop_id=shop_id or 0,
        scheduled_date=now,
        scheduled_time=time(9, 0),
        duration_minutes=booking.get("duration_minutes"),
        location_type=booking.get("location_type", "at_seller"),
        location_address=booking.get("location_address", ""),
        price=booking["price"],
        status=BookingStatus.PENDING,
        customer_phone=buyer.phone,
        customer_name=buyer.username,
    )
    db.add(booking_record)
    db.flush()

    seller = db.query(User).filter(User.id == seller_id).first() if seller_id else None
    shop = db.query(Shop).filter(Shop.id == shop_id).first() if shop_id else None

    if seller and seller.phone:
        _notify_via_whatsapp(
            seller.phone,
            f"📅 *New Booking Request #{booking_record.id}!*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📦 {booking['service_title']}\n"
            f"💰 KSh {booking['price']:,.0f}\n"
            f"🗓️ {booking.get('scheduled_date_raw', 'TBD')} @ {booking.get('scheduled_time_raw', 'TBD')}\n"
            f"👤 {buyer.username} -- {buyer.phone}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"Check your dashboard: {settings.SITE_URL}/dashboard"
        )

    db.commit()
    del _pending_bookings[sender]

    loc_type_labels = {"at_seller": "at their location", "at_buyer": "at your location", "remote": "remotely"}
    loc_label = loc_type_labels.get(booking["location_type"], booking["location_type"])

    return (
        f"✅ *Booking Confirmed!* 🎉\n\n"
        f"📦 *{booking['service_title']}*\n"
        f"💰 KSh {booking['price']:,.0f}\n"
        f"🗓️ {booking.get('scheduled_date_raw', 'TBD')} @ {booking.get('scheduled_time_raw', 'TBD')}\n"
        f"📍 {loc_label}\n\n"
        f"The service provider has been notified and will confirm shortly.\n"
        f"Order #{booking_record.id} is now pending confirmation.\n\n"
        f"Need help? Just ask! 😊"
    )


def _process_booking_markers(reply: str, sender: str, db: Session) -> str | None:
    """Process booking markers from AI response. Returns a reply if an action was taken."""
    state = _pending_bookings.get(sender)
    if not state:
        return None

    step = state.get("step")

    # [BOOK:<service_id>] - initial booking marker
    m = _AI_BOOK_MARKER.search(reply)
    if m:
        service_id = int(m.group(1))
        service = db.query(Product).filter(Product.id == service_id).first()
        if service and _is_service(service):
            result = _start_booking_flow(sender, service, db)
            return result

    # [BOOK_DATE:<id>:<date>] - set date
    m = _AI_BOOK_DATE_MARKER.search(reply)
    if m and step == "choose_date":
        state["scheduled_date_raw"] = m.group(2).strip()
        state["step"] = "choose_time"
        clean = _AI_BOOK_DATE_MARKER.sub("", reply).strip()
        return clean + "\n\nGreat! What time would you prefer? (e.g., '10am', '2:30 PM')"

    # [BOOK_TIME:<id>:<time>] - set time
    m = _AI_BOOK_TIME_MARKER.search(reply)
    if m and step == "choose_time":
        state["scheduled_time_raw"] = m.group(2).strip()
        state["step"] = "choose_location"
        clean = _AI_BOOK_TIME_MARKER.sub("", reply).strip()
        shop = db.query(Shop).filter(Shop.id == state["shop_id"]).first() if state.get("shop_id") else None
        lines = [
            clean,
            "\n📍 Where would you like the service?",
            "\n1️⃣ At their location 🏪",
        ]
        if shop and shop.pickup_address:
            lines.append(f"   {shop.pickup_address}")
        lines.append("\n2️⃣ At my location 🏠")
        lines.append("3️⃣ Remote/Online 💻")
        return "\n".join(lines)

    # [BOOK_LOCATION:<id>:<type>] - set location type
    m = _AI_BOOK_LOCATION_MARKER.search(reply)
    if m and step == "choose_location":
        loc_type = m.group(2).strip().lower()
        state["location_type"] = loc_type
        state["step"] = "confirm"
        if loc_type == "at_buyer":
            state["step"] = "buyer_address"
            clean = _AI_BOOK_LOCATION_MARKER.sub("", reply).strip()
            return clean + "\n\nPlease share your address or location."
        clean = _AI_BOOK_LOCATION_MARKER.sub("", reply).strip()
        booking_summary = _show_booking_summary(sender, state, db)
        return f"{clean}\n\n{booking_summary}"

    # [BOOK_CONFIRM:<id>] - confirm booking
    if _AI_BOOK_CONFIRM.search(reply):
        result = _finalize_booking(sender, state, db)
        return result

    return None


def _build_booking_context(sender: str, db: Session) -> str | None:
    """Build AI context for the booking flow."""
    booking = _pending_bookings.get(sender)
    if not booking:
        return None
    step = booking.get("step")
    service = db.query(Product).filter(Product.id == booking["service_id"]).first()
    shop = db.query(Shop).filter(Shop.id == booking["shop_id"]).first() if booking.get("shop_id") else None

    lines = [
        "\n\n=== BOOKING FLOW ===",
        f"Service: {booking['service_title']}",
        f"Price: KSh {booking['price']:,.0f}",
        f"Current step: {step}",
    ]
    if booking.get("duration_minutes"):
        lines.append(f"Duration: ~{booking['duration_minutes']} minutes")
    if shop:
        lines.append(f"Shop: {shop.name} ({shop.location_area or 'N/A'})")

    if step == "choose_date":
        lines.append("\nAsk the user what DATE they want to book.")
        lines.append("When they provide it, use: [BOOK_DATE:<service_id>:<date>]")
    elif step == "choose_time":
        lines.append(f"\nDate chosen: {booking.get('scheduled_date_raw', '?')}")
        lines.append("Ask the user what TIME they prefer.")
        lines.append("When they provide it, use: [BOOK_TIME:<service_id>:<time>]")
    elif step == "choose_location":
        lines.append("\nAsk where they want the service:")
        lines.append("  - At shop: [BOOK_LOCATION:<id>:at_seller]")
        lines.append("  - At home: [BOOK_LOCATION:<id>:at_buyer]")
        lines.append("  - Remote: [BOOK_LOCATION:<id>:remote]")
    elif step == "buyer_address":
        lines.append("\nAsk for their address/location.")
        lines.append("When they provide it, use: [BOOK_LOCATION:<id>:at_buyer]")
    elif step == "confirm":
        lines.append("\nShow the booking summary and ask to confirm.")
        lines.append("To confirm: [BOOK_CONFIRM:<id>]")
        lines.append("To cancel: [CANCEL_FLOW]")

    lines.append("\nIMPORTANT: Be conversational. Guide naturally.")
    return "\n".join(lines)


_AI_ESCALATE = re.compile(r"\[ESCALATE:\s*(.+?)\]", re.IGNORECASE)


# ---------- Markers list ----------

_ALL_MARKERS = [
    _AI_BUY_MARKER, _AI_IMG_MARKER, _AI_OFFER_MARKER,
    _AI_ADD_PRODUCT, _AI_UPDATE_STOCK, _AI_UPDATE_PRICE,
    _AI_SET_STATUS, _AI_MARK_SHIPPED, _AI_CANCEL_ORDER,
    _AI_FULFILL_METHOD, _AI_FULFILL_PICKUP, _AI_FULFILL_LOCATION,
    _AI_FULFILL_CONFIRM, _AI_FULFILL_CANCEL,
    _AI_BUDGET_MARKER,
    _AI_BOOK_MARKER, _AI_BOOK_DATE_MARKER, _AI_BOOK_TIME_MARKER,
    _AI_BOOK_LOCATION_MARKER, _AI_BOOK_CONFIRM,
    _AI_ESCALATE,
]


def _translate_swahili(text: str) -> str:
    """Convert Swahili words to English for rule matching."""
    lower = text.strip().lower()
    words = lower.split()
    translated = []
    for w in words:
        translated.append(SWAHILI_KEYWORDS.get(w, w))
    return " ".join(translated)


def _strip_all_markers(text: str) -> str:
    for pat in _ALL_MARKERS:
        text = pat.sub("", text)
    return text.strip()


def _strip_fulfillment_markers(text: str) -> str:
    """Remove all fulfillment markers from text."""
    for pat in (_AI_FULFILL_METHOD, _AI_FULFILL_PICKUP, _AI_FULFILL_LOCATION, _AI_FULFILL_CONFIRM, _AI_FULFILL_CANCEL):
        text = pat.sub("", text)
    return text.strip()


def _process_fulfillment_markers(reply: str, sender: str, db: Session) -> str | None:
    """Process fulfillment markers from AI response. Returns a reply if an action was taken."""
    state = _load_state(sender)
    if not state:
        return None

    step = state.get("step")
    loaded = _load_items(state, db)
    first_product = loaded[0][0] if loaded else None
    shop = first_product.shop if first_product else None

    # [METHOD:delivery] or [METHOD:pickup]
    m = _AI_FULFILL_METHOD.search(reply)
    if m and step == "choose_method":
        method = m.group(1).lower()
        state["fulfillment_method"] = method
        clean = _AI_FULFILL_METHOD.sub("", reply).strip()
        if method == "delivery":
            state["step"] = "delivery_location"
            _save_state(sender, state)
            return clean + "\n\n📍 Great! Please share your delivery location or area (e.g., 'Westlands, Nairobi')."
        elif method == "pickup":
            state["step"] = "pickup_point"
            _save_state(sender, state)
            pickup_text = _get_pickup_points_text(db, shop)
            if pickup_text:
                return clean + f"\n\n{pickup_text}\n\nReply with the number of your preferred pickup point."
            else:
                return clean + "\n\n📍 Please type your preferred pickup area."

    # [PICKUP:<number>]
    m = _AI_FULFILL_PICKUP.search(reply)
    if m and step == "pickup_point":
        idx = int(m.group(1))
        points = db.query(PickupPoint).order_by(PickupPoint.area, PickupPoint.name).all()
        filtered = _filter_pickup_points(points, shop)
        if 1 <= idx <= len(filtered):
            pp = filtered[idx - 1]
            state["pickup_point_id"] = pp.id
            state["pickup_point_name"] = pp.name
            state["pickup_point_area"] = pp.area or ""
            state["step"] = "confirm"
            _save_state(sender, state)
            clean = _AI_FULFILL_PICKUP.sub("", reply).strip()
            summary = _build_order_summary(state, db)
            return f"{clean}\n\n{summary}\n\nReply ✅ *confirm* to place your order, or ❌ *cancel*."
        clean = _AI_FULFILL_PICKUP.sub("", reply).strip()
        return f"{clean}\n\nPlease select a valid pickup point number (1-{len(filtered)})."

    # [LOCATION:<area>]
    m = _AI_FULFILL_LOCATION.search(reply)
    if m and step == "delivery_location":
        location = m.group(1).strip()
        state["delivery_area"] = location
        state["step"] = "confirm"
        _save_state(sender, state)
        clean = _AI_FULFILL_LOCATION.sub("", reply).strip()
        summary = _build_order_summary(state, db)
        return f"{clean}\n\n{summary}\n\nReply ✅ *confirm* to place your order, or ❌ *cancel*."

    # [PLACE_ORDER]
    if _AI_FULFILL_CONFIRM.search(reply) and step == "confirm":
        result = _finalize_fulfillment(sender, db)
        _del_state(sender)
        clean = _AI_FULFILL_CONFIRM.sub("", reply).strip()
        return f"{clean}\n\n{result}" if clean else result

    # [CANCEL_FLOW]
    if _AI_FULFILL_CANCEL.search(reply):
        _del_state(sender)
        return _AI_FULFILL_CANCEL.sub("", reply).strip() + "\n\nOrder cancelled. Let me know if you need anything else! 😊"

    return None


def _build_order_summary(state: dict, db: Session) -> str:
    """Build a structured checkout summary with all items and fulfillment info."""
    items = _load_items(state, db)
    if not items:
        return "No items in your order."

    method = state.get("fulfillment_method", "pickup")
    if method == "delivery":
        loc_label = state.get("delivery_area", "To be confirmed")
        header = f"📍 *Delivery:* {loc_label}"
        fee_line = ""
    else:
        pname = state.get("pickup_point_name", "Shop")
        parea = state.get("pickup_point_area", "")
        loc_label = f"{pname}" + (f" ({parea})" if parea else "")
        header = f"📍 *Pickup:* {loc_label}"
        fee_line = ""

    subtotal = sum(p.price * qty for p, qty in items)

    lines = [
        "📋 *Checkout Summary*",
        "━━━━━━━━━━━━━━━━━━━",
    ]
    for p, qty in items:
        sname = p.shop.name if p.shop else "Ikobiz"
        lines.append(f"• {p.title} × {qty}")
        lines.append(f"  KSh {p.price:,.0f} each — KSh {p.price * qty:,.0f}")
        lines.append(f"  🏪 {sname}")

    lines.append("")
    lines.append(header)
    lines.append(f"💳 *Payment:* M-Pesa")
    if fee_line:
        lines.append(fee_line)
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"*Total:* KSh {subtotal:,.0f}")
    lines.append("━━━━━━━━━━━━━━━━━━━")

    return "\n".join(lines)


def _finalize_fulfillment(sender: str, db: Session) -> str:
    """Create the order with all items/quantities from the flow. Supports both delivery and pickup."""
    state = _load_state(sender)
    if not state:
        return "Sorry, something went wrong. Please start again."

    items = _load_items(state, db)
    if not items:
        return "Sorry, your order is empty."

    for product, qty in items:
        if product.stock < qty:
            return f"Sorry, {product.title} only has {product.stock} available (you requested {qty})."

    buyer = _find_or_create_buyer(db, sender)
    subtotal = sum(p.price * qty for p, qty in items)
    first_product = items[0][0]
    shop = first_product.shop
    seller = db.query(User).filter(User.id == shop.owner_id).first() if shop else None
    store_label = shop.name if shop else "Ikobiz Platform"
    method = state.get("fulfillment_method", "pickup")
    item_lines = ", ".join(f"{p.title} × {qty}" for p, qty in items)

    if method == "delivery":
        delivery_area = state.get("delivery_area", "Nairobi")
        fulfillment_method = "seller_delivery"
        delivery_fee_val = shop.delivery_fee if (shop and shop.delivery_fee) else 0
        total = subtotal + delivery_fee_val
        loc_label = delivery_area
    else:
        fulfillment_method = "pickup"
        delivery_fee_val = 0
        total = subtotal
        pname = state.get("pickup_point_name", "Shop")
        parea = state.get("pickup_point_area", "")
        loc_label = f"{pname}" + (f" ({parea})" if parea else "")

    order = Order(
        buyer_id=buyer.id,
        total=total,
        status=OrderStatus.PENDING,
        fulfillment_method=fulfillment_method,
        delivery_area=loc_label,
        delivery_fee=delivery_fee_val,
        payment_method="mpesa",
        payment_status="pending",
        customer_phone=sender.replace("+", "").replace(" ", ""),
        customer_name=buyer.username,
    )
    db.add(order)
    db.flush()

    for product, qty in items:
        order_item = OrderItem(order_id=order.id, product_id=product.id, price=product.price, quantity=qty)
        db.add(order_item)
        product.stock -= qty

    if seller:
        db.add(Message(
            order_id=order.id, sender_id=seller.id,
            content=(
                f"Thank you for shopping at {store_label}! "
                f"Your order #{order.id} has been received. "
                f"{'Your items will be delivered to ' + loc_label if method == 'delivery' else 'Your items will be ready for pickup at ' + loc_label}. "
                f"We appreciate your business!"
            ),
            is_auto_reply=True,
        ))
        db.add(Message(
            order_id=order.id, sender_id=buyer.id,
            content=(
                f"New WhatsApp Order #{order.id} from {buyer.username}!\n"
                f"Items: {item_lines}\n"
                f"Total: KSh {total:,.0f}\n"
                f"{'Delivery: ' + loc_label if method == 'delivery' else 'Pickup: ' + loc_label}\n"
                f"Buyer phone: {buyer.phone}\n"
                f"Please prepare the order.\n"
                f"Payment: Pending M-Pesa confirmation."
            ),
            is_auto_reply=True,
        ))
        if seller.phone:
            method_label = "Delivery" if method == "delivery" else "Pickup"
            _notify_via_whatsapp(
                seller.phone,
                f"📦 *New Order #{order.id} ({method_label})!*\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"Items: {item_lines}\n"
                f"Total: KSh {total:,.0f}\n"
                f"{method_label}: {loc_label}\n"
                f"Buyer WhatsApp: {buyer.phone}\n"
                f"Payment: Pending M-Pesa\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"Manage: {settings.SITE_URL}/dashboard"
            )

    db.commit()

    # Initiate M-Pesa STK Push in background
    clean_phone = sender.replace("+", "").replace(" ", "").replace("-", "")
    if clean_phone.startswith("254") or clean_phone.startswith("0"):
        if clean_phone.startswith("0"):
            clean_phone = "254" + clean_phone[1:]
        _initiate_mpesa_payment_async(order.id, total, clean_phone, db)

    method_icon = "🚚" if method == "delivery" else "📍"
    lines = [
        "✅ *Order Confirmed!*",
        "━━━━━━━━━━━━━━━━━━━",
    ]
    for p, qty in items:
        sname = p.shop.name if p.shop else "Ikobiz"
        lines.append(f"• {p.title} × {qty} — KSh {p.price * qty:,.0f}")
        lines.append(f"  🏪 {sname}")
    lines.append("")
    lines.append(f"{method_icon} *{method.title()}:* {loc_label}")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"*Total:* KSh {total:,.0f}")
    lines.append("━━━━━━━━━━━━━━━━━━━")
    lines.append(f"\n💰 *M-Pesa payment of KSh {total:,.0f} sent to your phone!*")
    lines.append(f"📱 Check your phone, enter your M-Pesa PIN to complete payment.")
    lines.append(f"\n✅ Order #{order.id} placed with {store_label}.")
    lines.append(f"\n📱 The seller has your WhatsApp number and will contact you after payment clears.")

    if seller and seller.phone:
        clean_seller_phone = seller.phone.replace("+", "").replace(" ", "").replace("-", "")
        lines.append(f"📲 *Chat with seller:* https://wa.me/{clean_seller_phone}")

    return "\n".join(lines)


def _initiate_mpesa_payment_async(order_id: int, amount: float, phone: str, db: Session):
    """Fire-and-forget M-Pesa STK Push in a background thread."""
    import threading
    def _do_push():
        import asyncio
        from core.database import SessionLocal
        from services.daraja import stk_push
        from models import Payment, PaymentStatus

        session = SessionLocal()
        try:
            resp = asyncio.run(stk_push(
                phone=phone,
                amount=amount,
                account_ref=f"IKO{order_id}",
                transaction_desc=f"Ikobiz Order {order_id}",
            ))
            result_code = resp.get("ResponseCode")
            payment = Payment(
                order_id=order_id,
                amount=amount,
                phone=phone,
                checkout_request_id=resp.get("CheckoutRequestID"),
                merchant_request_id=resp.get("MerchantRequestID"),
                status=PaymentStatus.PENDING.value if result_code == "0" else PaymentStatus.FAILED.value,
            )
            session.add(payment)
            session.commit()

            if result_code != "0":
                from app.whatsapp.service import send_text_message_sync
                send_text_message_sync(
                    phone,
                    f"⚠️ M-Pesa payment failed for Order #{order_id}. "
                    f"Please use the web dashboard to try again: {settings.SITE_URL}/checkout/{order_id}",
                )
        except Exception as e:
            logger.error(f"M-Pesa background push failed for order #{order_id}: {e}")
        finally:
            session.close()

    thread = threading.Thread(target=_do_push, daemon=True)
    thread.start()


def _find_or_create_buyer(db: Session, phone: str) -> User:
    """Look up a user by WhatsApp phone number, or create them as a buyer."""
    user = db.query(User).filter(User.phone == phone).first()
    if user:
        return user

    safe_phone = phone.replace("+", "").replace(" ", "")
    username = f"wa_{safe_phone}"
    email = f"{safe_phone}@whatsapp.ikobiz.com"

    attempt = 0
    while db.query(User).filter(User.username == username).first():
        attempt += 1
        username = f"wa_{safe_phone}_{attempt}"
    while db.query(User).filter(User.email == email).first():
        email = f"{safe_phone}_{attempt}@whatsapp.ikobiz.com"

    user = User(
        username=username,
        email=email,
        phone=safe_phone,
        password_hash=hash_password(secrets.token_urlsafe(16)),
        role="buyer",
    )
    db.add(user)
    db.flush()
    logger.info(f"Created WhatsApp buyer user: {username} ({phone})")
    return user


# ---------- Rule-based purchase processing ----------

PURCHASE_KEYWORDS = {"buy", "purchase", "order", "procure"}
STOP_WORDS = {"a", "an", "the", "to", "for", "of", "in", "on", "at", "is", "i", "me", "my", "we", "our", "some", "please", "can", "could", "would", "will", "with", "and", "or", "have", "has", "get", "want", "need", "looking"}


def _is_purchase_intent(text: str) -> bool:
    """Detect if the message signals purchase intent."""
    lower = text.strip().lower()
    if not lower:
        return False
    if re.match(r"^\d{1,2}$", lower):
        return True
    if re.match(r"^buy\s+(\d{1,2})$", lower):
        return True
    for kw in PURCHASE_KEYWORDS:
        if lower.startswith(kw) or f" {kw} " in f" {lower} ":
            return True
    return False


def _extract_product_query(text: str) -> str:
    """Remove purchase keywords and stop words to get the core product name."""
    lower = text.strip().lower()
    for kw in sorted(PURCHASE_KEYWORDS, key=len, reverse=True):
        lower = lower.replace(kw, " ", 1).strip()
    words = [w for w in lower.split() if w not in STOP_WORDS]
    query = " ".join(words).strip(" ,.!?:;")
    return query


def _process_whatsapp_purchase(db: Session, sender: str, text: str) -> str | None:
    """
    Attempt to process a purchase from a WhatsApp message.
    Supports numbered selection (1, 2, 3) from previous search results.
    Supports quantity prefix like '5 kale' or 'buy 3 phones'.
    """
    lower = text.strip().lower()

    m = re.match(r"^(?:buy\s+)?(\d{1,2})$", lower)
    if m and sender in _pending_selections:
        idx = int(m.group(1)) - 1
        pending = _pending_selections[sender]
        products = pending.get("products", [])
        total = len(products)

        if idx < 0 or idx >= total:
            return f"Please pick a number between 1 and {total}."

        del _pending_selections[sender]

        product = products[idx]
        if product.stock < 1:
            return f"Sorry, {product.title} is currently out of stock."
        return _start_fulfillment_flow(sender, [(product, 1)], db)

    qty = 1
    qty_parse = re.match(r"^(?:buy\s+)?(\d+)\s+(.+)$", lower)
    if qty_parse:
        qty = int(qty_parse.group(1))
        query = _extract_product_query(qty_parse.group(2))
    else:
        query = _extract_product_query(text)

    if not query or len(query) < 2:
        return "What product would you like to buy? Send the product name after 'buy'."

    products = (
        db.query(Product)
        .filter(
            Product.status == ProductStatus.ACTIVE,
            Product.title.ilike(f"%{query}%"),
        )
        .all()
    )

    total_matches = len(products)

    words = [w for w in query.split() if len(w) > 2]

    if total_matches == 0:
        for w in words:
            products = (
                db.query(Product)
                .filter(
                    Product.status == ProductStatus.ACTIVE,
                    Product.title.ilike(f"%{w}%"),
                )
                .all()
            )
            total_matches = len(products)
            if total_matches > 0:
                break

    if total_matches == 0:
        for w in words:
            if len(w) >= 4:
                prefix = w[:4]
                products = (
                    db.query(Product)
                    .filter(
                        Product.status == ProductStatus.ACTIVE,
                        Product.title.ilike(f"%{prefix}%"),
                    )
                    .all()
                )
                total_matches = len(products)
                if total_matches > 0:
                    break

    if total_matches == 0:
        return (
            f"Sorry, I couldn't find a product matching \"{query}\" in our catalog.\n\n"
            f"Try sending \"shops\" to see all available shops, or browse at {settings.SITE_URL}"
        )

    if total_matches > 1:
        _pending_selections[sender] = {
            "products": products,
        }

        msg = f"Found {total_matches} product(s) matching \"{query}\":\n\n"
        idx = 1
        for p in products:
            shop_name = p.shop.name if p.shop else "N/A"
            msg += f"{idx}. {p.title} -- KSh {p.price:,.0f} ({shop_name})\n"
            idx += 1
        msg += "\nReply with the number (1, 2, 3...) to purchase."
        return msg

    if products:
        product = products[0]
        if product.stock < qty:
            return f"Sorry, {product.title} only has {product.stock} available (you requested {qty})."
        return _start_fulfillment_flow(sender, [(product, qty)], db)

    return None


# ---------- WhatsApp cancellation flow ----------

CANCEL_KEYWORDS = {"cancel", "cancel order", "cancel my order", "cancel my purchase", "i want to cancel", "i need to cancel", "stop order"}


def _is_cancellation_intent(text: str) -> bool:
    lower = text.strip().lower()
    return any(kw in lower for kw in CANCEL_KEYWORDS)


def _process_whatsapp_cancellation(sender: str, text: str, db: Session) -> str:
    """Handle customer cancellation request from WhatsApp."""
    phone = sender.replace("+", "").replace(" ", "")
    orders = (
        db.query(Order)
        .filter(
            Order.customer_phone == phone,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED]),
        )
        .order_by(Order.created_at.desc())
        .all()
    )

    if not orders:
        return (
            "I couldn't find any active orders to cancel. "
            "You can only cancel orders that are still PENDING or CONFIRMED. "
            "Once an order is DISPATCHED or DELIVERED, it can't be cancelled."
        )

    if len(orders) == 1:
        return _cancel_whatsapp_order(orders[0], db)

    # Multiple cancellable orders -- store in pending and ask
    _pending_cancellations[sender] = orders
    msg = f"Found {len(orders)} order(s) that can be cancelled:\n\n"
    for i, o in enumerate(orders, 1):
        item_names = "; ".join(
            f"{oi.product.title} x{oi.quantity}" for oi in o.items if oi.product
        ) or f"Order #{o.id}"
        msg += f"{i}. #{o.id} -- {item_names} -- {_format_ksh(o.total)}\n"
    msg += "\nReply with the number (1, 2, 3...) to cancel that order."
    return msg


def _cancel_whatsapp_order(order: Order, db: Session) -> str:
    """Cancel a single order and notify the seller via WhatsApp."""
    order.status = OrderStatus.CANCELLED
    db.commit()

    # Notify seller
    seller_phones = set()
    seller_user = None
    for oi in order.items:
        if oi.product_id:
            product = db.query(Product).filter(Product.id == oi.product_id).first()
            if product and product.shop and product.shop.owner_id:
                seller = db.query(User).filter(User.id == product.shop.owner_id).first()
                if seller and seller.phone:
                    seller_phones.add(seller.phone)
                    seller_user = seller

    cancel_msg = (
        f"❌ Order #{order.id} Cancelled by Customer\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"The customer cancelled their order via WhatsApp.\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Check your dashboard: {settings.SITE_URL}/dashboard"
    )
    for phone in seller_phones:
        _notify_via_whatsapp(phone, cancel_msg)

    if seller_user:
        buyer = db.query(User).filter(User.id == order.buyer_id).first()
        if buyer:
            db.add(Message(
                order_id=order.id, sender_id=seller_user.id,
                content=f"Order #{order.id} has been cancelled by the customer via WhatsApp.",
                is_auto_reply=True,
            ))
            db.commit()

    return (
        f"✅ Order #{order.id} has been cancelled.\n\n"
        f"The seller has been notified. If you need anything else, just let me know!"
    )


# ---------- Seller action handler ----------


def _process_seller_action(sender: str, text: str, db: Session) -> str | None:
    """Handle seller's number reply to an order or offer notification."""
    lower = text.strip().lower()
    if sender not in _pending_seller_actions:
        return None

    action = _pending_seller_actions[sender]

    if action.get("action") == "new_offer":
        return _process_offer_response(sender, lower, action, db)

    order_id = action["order_id"]
    buyer_name = action["buyer_name"]
    buyer_phone = action["buyer_phone"]
    product_title = action["product_title"]
    store_label = action["store_label"]

    if lower == "1" or lower.startswith("accept"):
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = OrderStatus.CONFIRMED
            db.commit()
        del _pending_seller_actions[sender]
        msg = (
            f"✅ Order #{order_id} accepted!\n\n"
            f"Product: {product_title}\n"
            f"Shop: {store_label}\n"
        )
        if order:
            if order.fulfillment_method:
                method = "Seller delivers" if order.fulfillment_method == "seller_delivery" else "Buyer picks up"
                msg += f"🚚 Fulfillment: {method}\n"
            if order.delivery_area:
                msg += f"📍 Location: {order.delivery_area}\n"
        msg += (
            f"\nPlease prepare it for shipping. You can mark it as shipped from your dashboard:\n"
            f"{settings.SITE_URL}/dashboard"
        )
        return msg

    if lower == "2" or lower.startswith("contact"):
        del _pending_seller_actions[sender]
        msg = (
            f"📞 Buyer contact:\n\n"
            f"Name: {buyer_name}\n"
            f"Phone: {buyer_phone}\n"
        )
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            if order.fulfillment_method:
                method = "Seller delivers" if order.fulfillment_method == "seller_delivery" else "Buyer picks up"
                msg += f"🚚 Fulfillment: {method}\n"
            if order.delivery_area:
                msg += f"📍 Location: {order.delivery_area}\n"
        msg += f"\nReach out to confirm the order and arrange delivery."
        return msg

    if lower == "3" or lower.startswith("back"):
        return (
            f"Order #{order_id} still pending.\n\n"
            f"Reply:\n"
            f"1 ✅ Accept order\n"
            f"2 📞 Contact buyer"
        )

    return None


def _process_offer_response(sender: str, lower: str, action: dict, db: Session) -> str | None:
    """Handle seller's response to an offer (accept/decline/counter)."""
    offer_id = action["offer_id"]
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer or offer.status != OfferStatus.PENDING:
        del _pending_seller_actions[sender]
        return "This offer is no longer pending."

    buyer_name = action["buyer_name"]
    buyer_phone = action["buyer_phone"]
    product_title = action["product_title"]
    amount = action["amount"]

    if lower == "1" or lower.startswith("accept"):
        offer.status = OfferStatus.ACCEPTED
        product = db.query(Product).filter(Product.id == offer.product_id).first()
        if product and product.stock >= 1:
            buyer = db.query(User).filter(User.id == offer.buyer_id).first()
            if buyer:
                order = Order(buyer_id=buyer.id, total=amount, status=OrderStatus.CONFIRMED)
                db.add(order)
                db.flush()
                item = OrderItem(order_id=order.id, product_id=product.id, price=amount, quantity=1)
                db.add(item)
                product.stock -= 1
                _notify_via_whatsapp(
                    buyer.phone,
                    f"🎉 *Offer Accepted!*\n\n"
                    f"Your offer of KSh {amount:,.0f} for *{product_title}* "
                    f"has been accepted by the seller!\n"
                    f"Order #{order.id} has been created.\n"
                    f"Thank you for shopping on Ikobiz! 🙏"
                )
        db.commit()
        del _pending_seller_actions[sender]
        return f"✅ Offer accepted! KSh {amount:,.0f} for {product_title}. Order created."

    if lower == "2" or lower.startswith("decline"):
        offer.status = OfferStatus.DECLINED
        if buyer_phone:
            _notify_via_whatsapp(
                buyer_phone,
                f"❌ Offer Declined\n\n"
                f"The seller declined your offer of KSh {amount:,.0f} "
                f"for *{product_title}*.\n\n"
                f"You can try a different offer or buy at full price."
            )
        db.commit()
        del _pending_seller_actions[sender]
        return f"❌ Offer for {product_title} declined. The buyer has been notified."

    if lower == "3" or lower.startswith("counter"):
        del _pending_seller_actions[sender]
        _pending_seller_actions[sender] = {
            "action": "counter_amount",
            "offer_id": offer_id,
            "buyer_name": buyer_name,
            "buyer_phone": buyer_phone,
            "product_title": product_title,
        }
        return (
            f"💬 What amount would you like to counter with?\n\n"
            f"Just type the amount (e.g., 35000)"
        )

    return None


def _process_counter_amount(sender: str, text: str, db: Session) -> str:
    """Handle seller typing a counter-offer amount."""
    action = _pending_seller_actions.pop(sender, None)
    if not action:
        return "Something went wrong. Please try again."

    try:
        amount = float(text.replace(",", "").replace("ksh", "").replace("KSh", "").strip())
    except ValueError:
        _pending_seller_actions[sender] = action
        return "Please type a valid number (e.g., 35000)"

    offer_id = action["offer_id"]
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer or offer.status != OfferStatus.PENDING:
        return "This offer is no longer pending."

    offer.status = OfferStatus.COUNTERED
    offer.seller_response = amount
    db.commit()

    buyer_phone = action["buyer_phone"]
    product_title = action["product_title"]
    _notify_via_whatsapp(
        buyer_phone,
        f"💬 *Counter Offer Received!*\n\n"
        f"The seller countered your offer for *{product_title}*.\n"
        f"Your offer: KSh {offer.amount:,.0f}\n"
        f"Seller's counter: *KSh {amount:,.0f}*\n\n"
        f"Reply to this bot to accept or negotiate further."
    )

    return f"💬 Counter offer of KSh {amount:,.0f} sent to {action['buyer_name']} for {product_title}."


# ---------- AI marker parsers ----------


def _process_ai_image_marker(ai_reply: str, db: Session) -> tuple[str, str | None, str | None]:
    """Strip [IMG:<id>] marker and return (cleaned_text, image_url, product_title)."""
    m = _AI_IMG_MARKER.search(ai_reply)
    if m:
        product_id = int(m.group(1))
        product = db.query(Product).filter(Product.id == product_id).first()
        if product and product.image_url:
            cleaned = _AI_IMG_MARKER.sub("", ai_reply).strip()
            return cleaned, product.image_url, product.title
    return ai_reply, None, None


def _process_ai_purchase_marker(ai_reply: str, sender: str, db: Session) -> str | None:
    """Check if AI response contains [BUY:<id>] or [BUY:<id>:<qty>] markers and initiate fulfillment flow."""
    matches = list(_AI_BUY_MARKER.finditer(ai_reply))
    if not matches:
        return None

    items = []
    for m in matches:
        product_id = int(m.group(1))
        qty = int(m.group(2)) if m.group(2) else 1

        product = db.query(Product).filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
        if not product:
            clean = _AI_BUY_MARKER.sub("", ai_reply).strip()
            return f"{clean}\n\nSorry, that product is no longer available."
        if product.stock < qty:
            clean = _AI_BUY_MARKER.sub("", ai_reply).strip()
            return f"{clean}\n\nSorry, {product.title} only has {product.stock} available (you requested {qty})."

        items.append((product, qty))

    clean = _AI_BUY_MARKER.sub("", ai_reply).strip()
    fulfillment_start = _start_fulfillment_flow(sender, items, db)
    return f"{clean}\n\n{fulfillment_start}"


# ---------- Seller marker processors ----------


def _strip_seller_markers(text: str) -> str:
    """Remove all seller action markers from text."""
    for pattern in (_AI_ADD_PRODUCT, _AI_UPDATE_STOCK, _AI_UPDATE_PRICE, _AI_SET_STATUS, _AI_MARK_SHIPPED):
        text = pattern.sub("", text)
    return text.strip()


def _process_seller_markers(ai_reply: str, seller: User, db: Session) -> tuple[str, list[str]]:
    """Process seller action markers and return (cleaned_text, confirmation_messages)."""
    confirmations = []

    for m in _AI_ADD_PRODUCT.finditer(ai_reply):
        shop_id, title, price_str, stock_str = int(m.group(1)), m.group(2).strip(), m.group(3), m.group(4)
        shop = db.query(Shop).filter(Shop.id == shop_id, Shop.owner_id == seller.id).first()
        if not shop:
            confirmations.append(f"Shop ID {shop_id} not found.")
            continue
        product = Product(
            shop_id=shop_id, title=title, price=float(price_str),
            stock=int(stock_str), status=ProductStatus.ACTIVE,
        )
        db.add(product)
        db.flush()
        confirmations.append(f"✅ Added '{title}' to {shop.name} at KSh {float(price_str):,.0f}")

    for m in _AI_UPDATE_STOCK.finditer(ai_reply):
        pid, new_stock = int(m.group(1)), int(m.group(2))
        p = db.query(Product).filter(Product.id == pid).first()
        if p and _is_seller_product(p, seller, db):
            p.stock = new_stock
            confirmations.append(f"✅ Stock for '{p.title}' updated to {new_stock}")
        else:
            confirmations.append(f"Product ID {pid} not found or not yours.")

    for m in _AI_UPDATE_PRICE.finditer(ai_reply):
        pid, new_price = int(m.group(1)), float(m.group(2))
        p = db.query(Product).filter(Product.id == pid).first()
        if p and _is_seller_product(p, seller, db):
            p.price = new_price
            confirmations.append(f"✅ Price for '{p.title}' updated to KSh {new_price:,.0f}")
        else:
            confirmations.append(f"Product ID {pid} not found or not yours.")

    for m in _AI_SET_STATUS.finditer(ai_reply):
        pid, status_str = int(m.group(1)), m.group(2).upper()
        p = db.query(Product).filter(Product.id == pid).first()
        if p and _is_seller_product(p, seller, db):
            try:
                p.status = ProductStatus(status_str)
                confirmations.append(f"✅ '{p.title}' is now {status_str}")
            except ValueError:
                confirmations.append(f"Invalid status '{status_str}'.")
        else:
            confirmations.append(f"Product ID {pid} not found or not yours.")

    for m in _AI_MARK_SHIPPED.finditer(ai_reply):
        oid = int(m.group(1))
        order = db.query(Order).filter(Order.id == oid).first()
        if order and _is_seller_order(order, seller, db):
            order.status = OrderStatus.DISPATCHED
            confirmations.append(f"✅ Order #{oid} marked as shipped!")
        else:
            confirmations.append(f"Order #{oid} not found or not yours.")

    if confirmations:
        db.commit()

    cleaned = _strip_seller_markers(ai_reply)
    return cleaned, confirmations


def _is_seller_product(product: Product, seller: User, db: Session) -> bool:
    shop = db.query(Shop).filter(Shop.id == product.shop_id).first()
    return shop is not None and shop.owner_id == seller.id


def _is_seller_order(order: Order, seller: User, db: Session) -> bool:
    for item in order.items:
        p = db.query(Product).filter(Product.id == item.product_id).first()
        if p:
            shop = db.query(Shop).filter(Shop.id == p.shop_id).first()
            if shop and shop.owner_id == seller.id:
                return True
    return False


# ---------- Buyer marker processors ----------


def _strip_buyer_markers(text: str) -> str:
    return _AI_CANCEL_ORDER.sub("", text).strip()


def _process_buyer_markers(ai_reply: str, buyer: User, db: Session) -> tuple[str, list[str]]:
    """Process buyer action markers and return (cleaned_text, confirmation_messages)."""
    confirmations = []

    for m in _AI_CANCEL_ORDER.finditer(ai_reply):
        oid = int(m.group(1))
        order = db.query(Order).filter(Order.id == oid, Order.buyer_id == buyer.id).first()
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            confirmations.append(f"✅ Order #{oid} has been cancelled.")
        elif order and order.status != OrderStatus.PENDING:
            confirmations.append(f"Order #{oid} is already {order.status.value} and cannot be cancelled.")
        else:
            confirmations.append(f"Order #{oid} not found.")

    if confirmations:
        db.commit()

    cleaned = _strip_buyer_markers(ai_reply)
    return cleaned, confirmations


# ---------- Offer marker processors ----------


def _strip_offer_markers(text: str) -> str:
    return _AI_OFFER_MARKER.sub("", text).strip()


def _process_offer_marker(ai_reply: str, sender: str, db: Session) -> tuple[str, list[str]]:
    """Process [OFFER:<product_id>:<amount>] marker -- notify seller, create Offer record."""
    confirmations = []
    m = _AI_OFFER_MARKER.search(ai_reply)
    if not m:
        return ai_reply, confirmations

    product_id, amount = int(m.group(1)), float(m.group(2))
    product = db.query(Product).filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE).first()
    if not product:
        confirmations.append("That product is no longer available.")
        return _strip_offer_markers(ai_reply), confirmations

    buyer = _find_or_create_buyer(db, sender)
    shop = product.shop
    seller = db.query(User).filter(User.id == shop.owner_id).first() if shop else None

    offer = Offer(buyer_id=buyer.id, product_id=product_id, amount=amount, status=OfferStatus.PENDING)
    db.add(offer)
    db.flush()

    if seller and seller.phone:
        _pending_seller_actions[seller.phone] = {
            "offer_id": offer.id,
            "action": "new_offer",
            "buyer_name": buyer.username,
            "buyer_phone": buyer.phone,
            "product_title": product.title,
            "store_label": shop.name if shop else "Ikobiz Platform",
            "amount": amount,
        }
        _notify_via_whatsapp(
            seller.phone,
            f"💰 *New Offer Received!*\n\n"
            f"🏪 Shop: *{shop.name if shop else 'Ikobiz'}*\n"
            f"📦 *{product.title}*\n"
            f"👤 From: {buyer.username} -- {buyer.phone}\n"
            f"💵 Offer: *KSh {amount:,.0f}*\n\n"
            f"Reply:\n"
            f"1 ✅ Accept offer\n"
            f"2 ❌ Decline\n"
            f"3 💬 Counter (type the amount)"
        )

    confirmations.append(
        f"✅ Your offer of KSh {amount:,.0f} for *{product.title}* "
        f"has been sent to {seller.username if seller else 'the seller'}! 🙏\n\n"
        f"They'll review it and get back to you shortly."
    )
    return _strip_offer_markers(ai_reply), confirmations


# ---------- Seller registration flow (WhatsApp onboarding) ----------

REG_STEPS = ["name", "shop_name", "location", "category", "phone", "confirm"]


def _is_in_seller_registration(sender: str) -> bool:
    return sender in _pending_seller_regs


def _handle_seller_registration(sender: str, text: str, db: Session) -> str | None:
    """Step-by-step seller registration via WhatsApp. Returns reply text or None if not in flow."""
    reg = _pending_seller_regs.get(sender)
    if not reg:
        return None

    step = reg.get("step")
    lower = text.strip()

    if step == "name":
        reg["name"] = lower
        reg["step"] = "shop_name"
        return f"Great, {lower}! 🎉\n\nWhat would you like to name your shop?"

    if step == "shop_name":
        reg["shop_name"] = lower
        reg["step"] = "location"
        return (
            f"'{lower}' — nice name! 🏪\n\n"
            f"What area/location is your shop based in? (e.g., Westlands, Nairobi)"
        )

    if step == "location":
        reg["location"] = lower
        reg["step"] = "category"
        return (
            f"{lower} — got it! 📍\n\n"
            f"What category best describes what you sell?\n"
            f"(e.g., Electronics, Fashion, Food, Health, Services, or anything else)"
        )

    if step == "category":
        reg["category"] = lower
        reg["step"] = "phone"
        return (
            f"{lower} — awesome! 🏷️\n\n"
            f"Lastly, what's your business phone number? "
            f"(Or reply *same* if it's the same as your WhatsApp number)"
        )

    if step == "phone":
        if lower.lower() in ("same", "same number", "this number", "my number"):
            reg["phone"] = sender.replace("+", "").replace(" ", "")
        else:
            reg["phone"] = lower.replace("+", "").replace(" ", "")
        reg["step"] = "confirm"
        summary = (
            f"📋 *Registration Summary*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: {reg['name']}\n"
            f"🏪 Shop: {reg['shop_name']}\n"
            f"📍 Location: {reg['location']}\n"
            f"🏷️ Category: {reg['category']}\n"
            f"📞 Phone: {reg['phone']}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"Reply ✅ *confirm* to create your shop, or ❌ *cancel* to start over."
        )
        return summary

    if step == "confirm":
        if lower.lower() in ("confirm", "yes", "ok", "yep", "sure", "✅"):
            return _finalize_seller_registration(sender, reg, db)
        else:
            del _pending_seller_regs[sender]
            return "No problem! Your registration has been cancelled. Let me know if you'd like to try again later. 😊"

    return None


def _finalize_seller_registration(sender: str, reg: dict, db: Session) -> str:
    """Create User + Shop from registration data."""
    safe_phone = reg["phone"]
    now_ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    username = f"slr_{safe_phone}_{now_ts}"
    email = f"{safe_phone}@seller.ikobiz.com"

    attempt = 0
    while db.query(User).filter(User.username == username).first():
        attempt += 1
        username = f"slr_{safe_phone}_{now_ts}_{attempt}"
    while db.query(User).filter(User.email == email).first():
        email = f"{safe_phone}_{attempt}@seller.ikobiz.com"

    user = User(
        username=username,
        email=email,
        phone=safe_phone,
        password_hash=hash_password(secrets.token_urlsafe(16)),
        role="seller",
    )
    db.add(user)
    db.flush()

    slug = re.sub(r"[^a-z0-9]+", "-", reg["shop_name"].lower()).strip("-")
    if not slug:
        slug = f"shop-{user.id}"
    existing = db.query(Shop).filter(Shop.slug == slug).first()
    if existing:
        slug = f"{slug}-{user.id}"

    shop = Shop(
        owner_id=user.id,
        name=reg["shop_name"],
        slug=slug,
        location_area=reg["location"],
        category=reg["category"],
        phone=safe_phone,
    )
    db.add(shop)
    db.commit()

    del _pending_seller_regs[sender]

    session = _get_or_create_session(sender, db)
    session.user_id = user.id
    session.role = "seller"
    session.updated_at = datetime.now(timezone.utc)
    db.commit()

    share_link = f"{settings.SITE_URL}/shops/{slug}"
    shop_link = f"{settings.SITE_URL}/seller/shops"

    return (
        f"🎉 *Welcome to Ikobiz, {reg['name']}!*\n\n"
        f"✅ Your account has been created\n"
        f"✅ Your shop *{reg['shop_name']}* is now live\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *Your Shop Link:*\n{share_link}\n\n"
        f"📊 *Dashboard:*\n{shop_link}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"Here's what you can do now:\n"
        f"1️⃣ *Add products* — Just say \"add product\" and I'll guide you! 📦\n"
        f"2️⃣ *Manage stock* — \"update stock for [product]\"\n"
        f"3️⃣ *Share your store* — Send the link above to customers 🚀\n\n"
        f"Need help? Just ask! 😊"
    )


# ---------- Product addition flow (WhatsApp-based) ----------

PRODUCT_STEPS = ["title", "price", "stock", "description", "confirm"]


def _is_in_product_addition(sender: str) -> bool:
    return sender in _pending_product_adds


def _start_product_addition(seller: User, db: Session) -> str | None:
    """Begin adding a product. Select shop if seller has multiple, otherwise go straight to title."""
    shops = db.query(Shop).filter(Shop.owner_id == seller.id).all()
    if not shops:
        return None

    if len(shops) == 1:
        _pending_product_adds[seller.phone] = {"shop_id": shops[0].id, "shop_name": shops[0].name, "step": "title"}
        return (
            f"Let's add a product to *{shops[0].name}!* 📦\n\n"
            f"What's the name of the product?"
        )

    _pending_product_adds[seller.phone] = {"shops": shops, "step": "select_shop"}
    msg = "Which shop would you like to add a product to?\n\n"
    for i, s in enumerate(shops, 1):
        msg += f"{i}. {s.name}\n"
    msg += "\nReply with the number."
    return msg


def _handle_product_addition(sender: str, text: str, db: Session) -> str | None:
    """Step-by-step product addition flow."""
    add = _pending_product_adds.get(sender)
    if not add:
        return None

    step = add.get("step")
    lower = text.strip()

    if step == "select_shop":
        shops = add.get("shops", [])
        if lower.isdigit():
            idx = int(lower) - 1
            if 0 <= idx < len(shops):
                add["shop_id"] = shops[idx].id
                add["shop_name"] = shops[idx].name
                add["step"] = "title"
                return f"Great! Adding to *{shops[idx].name}* 📦\n\nWhat's the name of the product?"
        return f"Please pick a number between 1 and {len(shops)}."

    if step == "title":
        add["title"] = lower
        add["step"] = "price"
        return f"*{lower}* — nice! 💫\n\nWhat's the price? (e.g., 25000)"

    if step == "price":
        try:
            price = float(lower.replace(",", "").replace("ksh", "").replace("KSh", "").replace("Ksh", "").strip())
            if price <= 0:
                raise ValueError
            add["price"] = price
            add["step"] = "stock"
            return f"KSh {price:,.0f} — got it! 💰\n\nHow many items do you have in stock? (e.g., 50)"
        except ValueError:
            return "Please enter a valid price (e.g., 25000)"

    if step == "stock":
        try:
            stock = int(lower.replace(",", "").strip())
            if stock < 0:
                raise ValueError
            add["stock"] = stock
            add["step"] = "description"
            return (
                f"{stock} units — noted! 📦\n\n"
                f"Add a short description (optional — type *skip* to continue without one)."
            )
        except ValueError:
            return "Please enter a valid number (e.g., 50)"

    if step == "description":
        if lower.lower() not in ("skip", "none", "no", "-"):
            add["description"] = lower
        add["step"] = "confirm"
        title = add.get("title", "?")
        price = add.get("price", 0)
        stock = add.get("stock", 0)
        desc = add.get("description", "(no description)")
        summary = (
            f"📋 *Product Summary*\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🏪 Shop: {add.get('shop_name', '?')}\n"
            f"📦 Product: {title}\n"
            f"💰 Price: KSh {price:,.0f}\n"
            f"📊 Stock: {stock}\n"
            f"📝 Description: {desc}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"Reply ✅ *confirm* to add, or ❌ *cancel* to discard."
        )
        return summary

    if step == "confirm":
        if lower.lower() in ("confirm", "yes", "ok", "yep", "sure", "✅"):
            return _finalize_product_addition(sender, add, db)
        else:
            del _pending_product_adds[sender]
            return "No problem! Product addition cancelled. 😊"

    return None


def _finalize_product_addition(sender: str, add: dict, db: Session) -> str:
    """Create the product from collected data."""
    product = Product(
        shop_id=add["shop_id"],
        title=add["title"],
        price=add["price"],
        stock=add["stock"],
        description=add.get("description", ""),
        status=ProductStatus.ACTIVE,
    )
    db.add(product)
    db.commit()

    del _pending_product_adds[sender]

    title = add["title"]
    price = add["price"]
    stock = add["stock"]
    product_id = product.id

    return (
        f"✅ *Product Added Successfully!* 🎉\n\n"
        f"📦 {title}\n"
        f"💰 KSh {price:,.0f}\n"
        f"📊 Stock: {stock}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"What would you like to do next?\n"
        f"▸ \"Add another product\" — to add more 📦\n"
        f"▸ \"[IMG:{product_id}]\" — to add a product image 📷\n"
        f"▸ \"Update stock\" — to change inventory 📊\n"
        f"▸ \"My shop link\" — to get your shareable store link 🔗\n\n"
        f"Just chat with me! 😊"
    )


# ---------- Shop link & context helpers ----------


def _get_shop_share_link(shop: Shop) -> str:
    """Generate a shareable link for a shop."""
    return f"{settings.SITE_URL}/shops/{shop.slug}"


def _get_seller_share_info(seller: User, db: Session) -> str | None:
    """Build share link info for all of a seller's shops."""
    shops = db.query(Shop).filter(Shop.owner_id == seller.id).all()
    if not shops:
        return None
    lines = ["🔗 *Your Shop Links*\n"]
    for s in shops:
        link = _get_shop_share_link(s)
        lines.append(f"🏪 *{s.name}*\n{link}\n")
    lines.append("Share these links with your customers! 🚀")
    return "\n".join(lines)


def _set_shop_context(sender: str, shop_slug: str, db: Session):
    """Set a shop context in the session so the AI focuses on this shop."""
    shop = db.query(Shop).filter(Shop.slug == shop_slug).first()
    if not shop:
        return
    session = _get_or_create_session(sender, db)
    state = {}
    if session.state:
        try:
            state = json.loads(session.state)
        except (json.JSONDecodeError, TypeError):
            state = {}
    state["shop_context"] = {"shop_id": shop.id, "shop_name": shop.name, "shop_slug": shop.slug}
    session.state = json.dumps(state)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()


def _clear_shop_context(sender: str, db: Session):
    """Clear the shop context from the session."""
    session = db.query(ChatSession).filter(ChatSession.sender == sender).first()
    if not session or not session.state:
        return
    try:
        state = json.loads(session.state)
        state.pop("shop_context", None)
        session.state = json.dumps(state) if state else None
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
    except (json.JSONDecodeError, TypeError):
        pass


def _get_shop_context(sender: str, db: Session) -> str | None:
    """Get current shop context from session, returns formatted string for AI."""
    session = db.query(ChatSession).filter(ChatSession.sender == sender).first()
    if not session or not session.state:
        return None
    try:
        state = json.loads(session.state)
        ctx = state.get("shop_context")
        if ctx:
            return (
                f"The user is currently browsing *{ctx['shop_name']}* (slug: {ctx['shop_slug']}).\n"
                f"Focus on products from this shop when answering questions.\n"
                f"Shop URL: {settings.SITE_URL}/shops/{ctx['shop_slug']}"
            )
    except (json.JSONDecodeError, TypeError):
        pass
    return None


# ---------- Main reply handler ----------


async def get_reply(text: str, sender: str, db: Session) -> tuple[str, str | None, str | None]:
    """
    AI-first conversational reply with rule-based fallback.
    Supports products AND services booking.
    Handles Swahili input.
    Returns (text, image_url, product_title).
    """

    stripped_lower = text.strip().lower()

    # Check for Swahili and translate for rule matching
    rule_text = _translate_swahili(stripped_lower)

    # 1. Booking flow (services)
    if _is_in_booking_flow(sender):
        booking_reply = _handle_booking_step(sender, text, db)
        if booking_reply:
            return booking_reply, None, None

    # 2. Fulfillment flow (delivery/location/payment/confirm)
    if _is_in_fulfillment_flow(sender):
        fulfillment_reply = _handle_fulfillment_step(sender, text, db)
        if fulfillment_reply:
            return fulfillment_reply, None, None

    # 3. Counter-offer amount entry
    if sender in _pending_seller_actions and _pending_seller_actions[sender].get("action") == "counter_amount":
        return _process_counter_amount(sender, stripped_lower, db), None, None

    # 4. Seller action (accept/decline order or offer)
    if sender in _pending_seller_actions:
        seller_reply = _process_seller_action(sender, stripped_lower, db)
        if seller_reply:
            return seller_reply, None, None

    # 5. Pending purchase selection (numbered)
    if sender in _pending_selections and re.match(r"^\d{1,2}$", stripped_lower):
        product_result = _process_whatsapp_purchase(db, sender, stripped_lower)
        if product_result:
            return product_result, None, None

    # 6. Pending cancellation selection (numbered)
    if sender in _pending_cancellations and re.match(r"^\d{1,2}$", stripped_lower):
        idx = int(stripped_lower) - 1
        orders = _pending_cancellations[sender]
        del _pending_cancellations[sender]
        if 0 <= idx < len(orders):
            return _cancel_whatsapp_order(orders[idx], db), None, None
        return f"Invalid selection. Please pick a number between 1 and {len(orders)}.", None, None

    # 7. Seller registration flow (step-by-step onboarding)
    if _is_in_seller_registration(sender):
        reg_reply = _handle_seller_registration(sender, text, db)
        if reg_reply:
            return reg_reply, None, None

    # 8. Product addition flow (step-by-step product creation)
    if _is_in_product_addition(sender):
        prod_reply = _handle_product_addition(sender, text, db)
        if prod_reply:
            return prod_reply, None, None

    # 9. Get or create session (persistent role tracking across messages)
    session = _get_or_create_session(sender, db)
    session = _sync_session_user(session, db)

    # 10. Detect seller/buyer from session
    seller = None
    buyer = None
    if session.role in ("seller", "admin"):
        seller = db.query(User).filter(User.id == session.user_id).first() if session.user_id else _get_seller(sender, db)
        if not seller and session.role == "seller":
            session.role = "buyer"
            db.commit()
    if not seller:
        buyer = db.query(User).filter(User.id == session.user_id).first() if session.user_id else _get_buyer(sender, db)

    # 11. Save user message to conversation history
    _save_conversation(sender, "user", text, db)

    # 12. Fetch recent conversation history
    history = _get_conversation_history(sender, db)

    # 13. Fetch role-specific context
    seller_context = _get_seller_context(seller, db) if seller else None
    buyer_context = _get_buyer_context(buyer, db) if buyer else None
    budget_context = _get_budget_context(sender) if not seller else None
    shop_context = _get_shop_context(sender, db)
    session_context = _get_session_context(session)
    if shop_context:
        session_context = (session_context or "") + f"\n\n{shop_context}"

    # 14. Build fulfillment/booking context if in flow
    fulfillment_context = _build_fulfillment_context(sender, db) if _is_in_fulfillment_flow(sender) else None
    booking_context = _build_booking_context(sender, db) if _is_in_booking_flow(sender) else None
    if booking_context:
        fulfillment_context = (fulfillment_context or "") + f"\n\n{booking_context}"

    # 15. Try AI
    db_context = _get_db_context_data(db)
    reply = await get_ai_reply(text, sender, db_context, history, seller_context, buyer_context, fulfillment_context, budget_context, session_context)
    if reply:
        _save_conversation(sender, "assistant", reply, db)

        # Process budget marker first (for any buyer)
        reply = _process_budget_marker(reply, sender)

        if seller:
            reply, confirmations = _process_seller_markers(reply, seller, db)
            if confirmations:
                reply += "\n\n" + "\n".join(confirmations)
        elif buyer:
            reply, confirmations = _process_buyer_markers(reply, buyer, db)
            if confirmations:
                reply += "\n\n" + "\n".join(confirmations)

        reply, offer_confirmations = _process_offer_marker(reply, sender, db)
        if offer_confirmations:
            reply += "\n\n" + "\n".join(offer_confirmations)

        # Process escalation marker
        escalation_match = _AI_ESCALATE.search(reply)
        if escalation_match:
            reason = escalation_match.group(1).strip()
            reply = _AI_ESCALATE.sub("", reply).strip()
            _escalated_sessions[sender] = True
            reply += (
                f"\n\n🆘 *I've flagged this for a human team member to help.*\n"
                f"Someone from Ikobiz will reach out to you shortly at this number.\n"
                f"Reason: {reason}"
            )

        reply, image_url, product_title = _process_ai_image_marker(reply, db)

        # During booking flow, process booking markers
        if _is_in_booking_flow(sender):
            booking_action = _process_booking_markers(reply, sender, db)
            if booking_action:
                reply = booking_action
            return _strip_all_markers(reply), image_url, product_title

        # During fulfillment flow, process fulfillment markers FIRST
        # and skip purchase markers (which would restart the flow)
        if _is_in_fulfillment_flow(sender):
            fulfillment_action = _process_fulfillment_markers(reply, sender, db)
            if fulfillment_action:
                reply = fulfillment_action
            return _strip_all_markers(reply), image_url, product_title

        purchase_result = _process_ai_purchase_marker(reply, sender, db)
        if purchase_result:
            return purchase_result, image_url, product_title

        return reply, image_url, product_title

    # 16. Rule-based fallback
    text = stripped_lower

    # Check for service booking intents
    service_keywords = {
        "book", "appointment", "schedule", "service", "fundi", "kinyozi", "mpishi",
        "tailor", "plumber", "mechanic", "barber", "cleaner", "tutor", "photographer",
        "book service", "i need a", "i want a", "nahitaji", "naomba",
    }
    if any(kw in rule_text or kw in text for kw in service_keywords):
        services = (
            db.query(Product)
            .filter(
                Product.status == ProductStatus.ACTIVE,
                Product.product_type == "service",
            )
            .all()
        )
        if services:
            msg = "🛠️ *Available Services*\n\n"
            for s in services:
                shop_name = s.shop.name if s.shop else "Ikobiz"
                dur = f" (~{s.service_duration_minutes}min)" if s.service_duration_minutes else ""
                msg += f"• *{s.title}* — KSh {s.price:,.0f}{dur} — {shop_name}\n"
            msg += "\nJust tell me which service you'd like to book! 😊"
            return msg, None, None

    if text in {"hi", "hello", "hey", "start", "menu", "help", "jambo", "habari", "mambo", "salam"}:
        return _welcome_message(db), None, None

    if text in {"shops", "list", "all shops", "maduka", "orodha"}:
        return _list_all_shops(db), None, None

    if _is_seller_registration_intent(text):
        return _seller_registration_reply(sender, db), None, None

    if _is_product_addition_intent(text) and seller:
        prod_reply = _start_product_addition(seller, db)
        if prod_reply:
            return prod_reply, None, None

    if _is_share_link_intent(text) and seller:
        links = _get_seller_share_info(seller, db)
        if links:
            return links, None, None

    if _is_purchase_intent(text):
        purchase_reply = _process_whatsapp_purchase(db, sender, text)
        if purchase_reply:
            return purchase_reply, None, None

    if _is_cancellation_intent(text):
        cancel_reply = _process_whatsapp_cancellation(sender, text, db)
        if cancel_reply:
            return cancel_reply, None, None

    search_text = text
    for prefix in ["i want ", "i need ", "looking for ", "find ", "search ", "show "]:
        if search_text.startswith(prefix):
            search_text = search_text[len(prefix):]
            break

    shops = db.query(Shop).filter(Shop.name.ilike(f"%{search_text}%")).all()
    if shops:
        return _format_shop_results(shops, search_text, db), None, None

    products = (
        db.query(Product)
        .filter(
            Product.status == ProductStatus.ACTIVE,
            Product.title.ilike(f"%{search_text}%"),
        )
        .all()
    )
    if products and len(products) <= 5:
        return _format_product_search_results(products, search_text), None, None

    return _help_text(), None, None


# ---------- Message formatters ----------


def _welcome_message(db: Session) -> str:
    shop_count = db.query(Shop).count()
    product_count = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
    service_count = db.query(Product).filter(Product.status == ProductStatus.ACTIVE, Product.product_type == "service").count()
    return (
        "🛍️ *Karibu Ikobiz!*\n\n"
        f"• {shop_count} shop(s) with {product_count} product(s)"
        + (f" and {service_count} service(s)" if service_count else "")
        + "\n\n"
        "👇 *Just tell me what you need! (Kiswahili pia)*\n"
        "▸ \"I want to buy a phone\" — nunua bidhaa\n"
        "▸ \"I need a plumber\" — tafuta fundi\n"
        "▸ \"Book a barber\" — weka booking\n"
        "▸ \"Nahitaji mpishi\" — find a cook\n\n"
        "I'll help you find, buy, or book in seconds 😊\n\n"
        "🛍️ *Want to sell?* Just say \"I want to sell\"!\n\n"
        "💬 I speak English and Swahili. Just chat with me!"
    )


def _list_all_shops(db: Session) -> str:
    shops = db.query(Shop).order_by(Shop.name).all()
    if not shops:
        return "No shops available yet. Check back soon!"
    msg = "🏪 *All Shops*\n\n"
    for s in shops:
        product_count = len(s.products) if s.products else 0
        link = f"{settings.SITE_URL}/shops/{s.slug}"
        loc = f" -- {s.location_area}" if s.location_area else ""
        modes = ""
        if s.fulfillment_modes:
            modes = f" ({s.fulfillment_modes.replace(',', ' + ').replace('_', ' ')})"
        msg += f"*{s.name}*{loc}\n📦 {product_count} product(s){modes}\n🔗 {link}\n\n"
    msg += "Send a product name to search across all shops!"
    return msg


def _format_shop_results(shops, query, db) -> str:
    msg = f"Found {len(shops)} shop(s) matching \"{query}\":\n\n"
    for s in shops:
        product_count = len(s.products) if s.products else 0
        link = f"{settings.SITE_URL}/shops/{s.slug}"
        msg += f"🏪 *{s.name}*\n"
        if s.description:
            desc = (s.description[:80] + "…") if len(s.description) > 80 else s.description
            msg += f"   {desc}\n"
        msg += f"📦 {product_count} product(s)\n🔗 {link}\n\n"
    msg += "Tap a link to browse and add items to your cart!"
    return msg


def _format_product_search_results(products, query) -> str:
    by_shop = defaultdict(list)
    for p in products:
        shop_name = p.shop.name if p.shop else "Unknown Shop"
        by_shop[shop_name].append(p)

    shop_names = list(by_shop.keys())
    if len(shop_names) == 1:
        msg = f"Found {len(products)} product(s) matching \"{query}\" in *{shop_names[0]}*:\n\n"
        for p in products:
            loc = f" -- {p.shop.location_area}" if p.shop and p.shop.location_area else ""
            msg += f"• *{p.title}* -- KSh {p.price:,.0f}{loc}\n"
        msg += "\nReply \"buy [product name]\" to purchase, or tap the link to browse:\n"
        msg += f"{settings.SITE_URL}/shops/{products[0].shop.slug if products[0].shop else ''}"
        return msg

    msg = f"Found {len(products)} product(s) matching \"{query}\" across {len(shop_names)} shops:\n\n"
    for shop_name in shop_names:
        shop_products = by_shop[shop_name]
        first_p = shop_products[0]
        loc = f" ({first_p.shop.location_area})" if first_p.shop and first_p.shop.location_area else ""
        msg += f"🏪 *{shop_name}*{loc}\n"
        for p in shop_products:
            msg += f"   • {p.title} -- KSh {p.price:,.0f}\n"
        if first_p.shop:
            msg += f"   🔗 {settings.SITE_URL}/shops/{first_p.shop.slug}\n"
        msg += "\n"
    msg += "Tap a link to browse, or send \"buy [product name]\" to purchase!"
    return msg


def _is_product_addition_intent(text: str) -> bool:
    lower = text.strip().lower()
    keywords = {
        "add product", "add item", "new product", "new item", "list product",
        "add a product", "upload product", "create product", "i want to add",
        "add goods", "add stock", "add inventory", "post product",
    }
    return any(kw in lower for kw in keywords)


def _is_share_link_intent(text: str) -> bool:
    lower = text.strip().lower()
    keywords = {
        "my shop link", "shop link", "share link", "my store link",
        "store link", "share my shop", "share my store", "get link",
        "my link", "shop url", "store url",
    }
    return any(kw in lower for kw in keywords)


def _is_seller_registration_intent(text: str) -> bool:
    lower = text.strip().lower()
    keywords = {
        "want to sell", "become a seller", "register as seller", "start selling",
        "open a shop", "create a shop", "register my shop", "list my products",
        "sell on ikobiz", "how to sell", "i want to sell", "can i sell",
        "seller registration", "join as seller", "become a vendor",
    }
    return any(kw in lower for kw in keywords)


def _seller_registration_reply(sender: str, db: Session) -> str:
    """Start the WhatsApp-based seller registration flow."""
    existing_seller = _get_seller(sender, db)
    if existing_seller:
        shops = db.query(Shop).filter(Shop.owner_id == existing_seller.id).all()
        if shops:
            links = _get_seller_share_info(existing_seller, db)
            return (
                f"🛍️ You're already registered as a seller! 🎉\n\n"
                f"{links}\n\n"
                f"Want to add more products? Just say *\"add product\"*! 📦"
            )

    _pending_seller_regs[sender] = {"step": "name"}
    return (
        "🛍️ *Great choice! Let's get you set up to sell on Ikobiz!* 🎉\n\n"
        "I'll guide you through it step by step. It only takes a minute! ⏱️\n\n"
        "First, what's your *name*? (Your business name or personal name)"
    )


def _help_text() -> str:
    return (
        "🤖 *Ikobiz Platform*\n\n"
        "Just chat with me naturally! 😊\n\n"
        "▸ \"I want to buy a phone\"\n"
        "▸ \"I need a plumber\" — Book a service\n"
        "▸ \"Nahitaji fundi\" — Kiswahili pia\n"
        "▸ \"What shops are there?\"\n"
        "▸ \"Show me laptops under 50k\"\n"
        "▸ \"I'll take the iPhone\"\n"
        "▸ \"Offer 30k for the Samsung\" -- Negotiate price\n\n"
        "*Want to sell?*\n"
        "▸ Say \"I want to sell\" to register right here on WhatsApp!\n\n"
        "*Already a seller:*\n"
        "▸ \"add product\" — add new items or services to your shop 📦\n"
        "▸ \"my shop link\" — get your shareable store link 🔗\n"
        "▸ \"update stock\" — change inventory 📊\n"
        "▸ \"update price\" — change product price 💰\n"
        "▸ When you get an order, reply 1 ✅ or 2 📞\n"
        "▸ When you get an offer, reply 1 ✅, 2 ❌, or 3 💬\n\n"
        "*Need other help?*\n"
        "▸ Just ask me anything -- I'm here to help! 😊\n\n"
        f"{settings.SITE_URL}"
    )


def _format_ksh(price: float) -> str:
    return "KSh " + f"{price:,.0f}"
