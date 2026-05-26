import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, IkobizListing, Negotiation, IkobizListingStatus
from app.whatsapp.service import send_text_message_sync

logger = logging.getLogger(__name__)

router = APIRouter(tags=["negotiations"])


class OfferCreate(BaseModel):
    buyer_name: str
    offer_price: float
    message: str | None = None
    is_counter_offer: bool = False


SITE_URL = "https://ikobiz.co.ke"


def _notify_whatsapp(phone: str | None, message: str):
    if phone:
        try:
            send_text_message_sync(phone, message)
        except Exception:
            logger.warning(f"Failed to send WhatsApp notification to {phone}")


@router.post("/ikobiz/products/{product_id}/offer", status_code=201)
def submit_offer(
    product_id: int,
    data: OfferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = db.query(IkobizListing).filter(IkobizListing.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ikobiz listing not found")
    if product.status == IkobizListingStatus.CLOSED:
        raise HTTPException(status_code=400, detail="This listing is closed for negotiations")

    offer = Negotiation(
        ikobiz_listing_id=product_id,
        buyer_name=data.buyer_name,
        offer_price=data.offer_price,
        message=data.message,
        is_counter_offer=1 if data.is_counter_offer else 0,
    )

    if product.status == IkobizListingStatus.OPEN:
        product.status = IkobizListingStatus.NEGOTIATING

    db.add(offer)
    db.commit()
    db.refresh(offer)

    if product.seller_id and product.seller_id != user.id:
        seller = db.query(User).filter(User.id == product.seller_id).first()
        if seller and seller.phone:
            _notify_whatsapp(
                seller.phone,
                f"💰 New Offer Received!\n\n"
                f"Listing: {product.title}\n"
                f"Buyer: {data.buyer_name}\n"
                f"Offer: {_format_ksh(data.offer_price)}\n"
                f"Message: {data.message or 'None'}\n\n"
                f"View & reply: {SITE_URL}/frontend/pages/ikobiz-item.html?id={product.id}"
            )

    return offer


@router.get("/ikobiz/products/{product_id}/offers")
def get_negotiation_history(product_id: int, db: Session = Depends(get_db)):
    product = db.query(IkobizListing).filter(IkobizListing.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ikobiz listing not found")

    offers = (
        db.query(Negotiation)
        .filter(Negotiation.ikobiz_listing_id == product_id)
        .order_by(Negotiation.created_at.asc())
        .all()
    )
    return offers


def _format_ksh(price: float) -> str:
    return "KSh " + f"{price:,.0f}"
