"""
routers/bookings.py - Service booking management endpoints.

GET    /bookings              - list bookings for current user (buyer or seller)
GET    /bookings/{id}         - get booking details
PATCH  /bookings/{id}/status  - update booking status (seller: confirm/cancel)
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_user
from models import User, Booking, BookingStatus, Product, Shop
from schemas.booking import BookingOut, BookingUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("")
def list_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List bookings for the current user. Buyers see their bookings; sellers see theirs."""
    if user.role in ("seller", "admin"):
        bookings = (
            db.query(Booking)
            .filter(Booking.seller_id == user.id)
            .order_by(Booking.created_at.desc())
            .all()
        )
    else:
        bookings = (
            db.query(Booking)
            .filter(Booking.buyer_id == user.id)
            .order_by(Booking.created_at.desc())
            .all()
        )

    result = []
    for b in bookings:
        service = db.query(Product).filter(Product.id == b.service_id).first()
        shop = db.query(Shop).filter(Shop.id == b.shop_id).first()
        result.append({
            "id": b.id,
            "service_id": b.service_id,
            "buyer_id": b.buyer_id,
            "seller_id": b.seller_id,
            "shop_id": b.shop_id,
            "scheduled_date": b.scheduled_date.isoformat() if b.scheduled_date else None,
            "scheduled_time": b.scheduled_time.strftime("%H:%M") if b.scheduled_time else None,
            "duration_minutes": b.duration_minutes,
            "location_type": b.location_type,
            "location_address": b.location_address,
            "price": b.price,
            "status": b.status.value if hasattr(b.status, 'value') else b.status,
            "customer_phone": b.customer_phone,
            "customer_name": b.customer_name,
            "seller_notes": b.seller_notes,
            "customer_notes": b.customer_notes,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "service_title": service.title if service else "Unknown Service",
            "shop_name": shop.name if shop else "Unknown Shop",
        })
    return result


@router.get("/{booking_id}")
def get_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.buyer_id != user.id and booking.seller_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return booking


@router.patch("/{booking_id}/status")
def update_booking_status(booking_id: int, data: BookingUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update booking status. Only the seller can confirm/cancel/completed."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.seller_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the service provider can update booking status")

    booking.status = BookingStatus(data.status)
    if data.seller_notes:
        booking.seller_notes = data.seller_notes
    db.commit()

    return {"message": f"Booking #{booking_id} status updated to {data.status}"}
