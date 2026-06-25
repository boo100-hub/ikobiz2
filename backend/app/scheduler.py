"""
scheduler.py - Background scheduler for booking reminders and proactive messages.

Run this as a separate process or via a cron job:
    python -m app.scheduler

It checks the database every 5 minutes for:
- Upcoming bookings (24h and 2h before) -> sends WhatsApp reminders
- Broadcasts scheduled for now -> triggers sending
"""

import logging
import time
from datetime import datetime, date, time as dtime, timedelta, timezone

from core.database import SessionLocal
from models import Booking, BookingStatus, Broadcast, BroadcastStatus, BroadcastOptIn, Shop

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")


def send_whatsapp(phone: str, message: str):
    try:
        from app.whatsapp.service import send_text_message_sync
        send_text_message_sync(phone, message)
    except Exception as e:
        logger.warning(f"Failed to send WhatsApp to {phone}: {e}")


def check_booking_reminders():
    """Send reminders for upcoming bookings."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        today = date.today()
        in_24h = now + timedelta(hours=24)
        in_2h = now + timedelta(hours=2)

        bookings = (
            db.query(Booking)
            .filter(
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
                Booking.scheduled_date >= today,
            )
            .all()
        )

        for b in bookings:
            if not b.scheduled_date or not b.scheduled_time:
                continue

            scheduled_dt = datetime.combine(b.scheduled_date, b.scheduled_time, tzinfo=timezone.utc)
            time_until = scheduled_dt - now

            if timedelta(hours=23) < time_until <= timedelta(hours=25):
                # 24-hour reminder
                if b.customer_phone:
                    send_whatsapp(
                        b.customer_phone,
                        f"⏰ *Reminder: Tomorrow!*\n\n"
                        f"You have a booking for *{b.service.title if b.service else 'a service'}* "
                        f"tomorrow at {b.scheduled_time.strftime('%I:%M %p')}.\n\n"
                        f"📍 {b.location_type.replace('_', ' ').title()}\n"
                        f"📞 Reply if you need to reschedule.",
                    )
                logger.info(f"Sent 24h reminder for booking #{b.id}")

            elif timedelta(hours=1.5) < time_until <= timedelta(hours=2.5):
                # 2-hour reminder
                if b.customer_phone:
                    send_whatsapp(
                        b.customer_phone,
                        f"⏰ *Reminder: Coming up soon!*\n\n"
                        f"Your booking for *{b.service.title if b.service else 'a service'}* "
                        f"is in about 2 hours at {b.scheduled_time.strftime('%I:%M %p')}.\n\n"
                        f"📍 {b.location_type.replace('_', ' ').title()}\n"
                        f"Enjoy your service! 😊",
                    )
                logger.info(f"Sent 2h reminder for booking #{b.id}")

    except Exception as e:
        logger.error(f"Booking reminders check failed: {e}")
    finally:
        db.close()


def check_scheduled_broadcasts():
    """Send broadcasts that are scheduled for now."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        broadcasts = (
            db.query(Broadcast)
            .filter(
                Broadcast.status == BroadcastStatus.SCHEDULED,
                Broadcast.scheduled_at <= now,
            )
            .all()
        )

        for b in broadcasts:
            optins = db.query(BroadcastOptIn).filter(
                BroadcastOptIn.shop_id == b.shop_id,
                BroadcastOptIn.opted_in == True,
            ).all()

            sent = 0
            for optin in optins:
                msg = f"📢 *{b.title}*\n\n{b.message}"
                if b.image_url:
                    msg += f"\n\n{b.image_url}"
                msg += "\n\n---\nReply STOP to unsubscribe"
                send_whatsapp(optin.phone, msg)
                sent += 1

            b.status = BroadcastStatus.SENT
            b.sent_count = sent
            b.sent_at = now
            db.commit()
            logger.info(f"Sent scheduled broadcast #{b.id} to {sent} customers")

    except Exception as e:
        logger.error(f"Scheduled broadcasts check failed: {e}")
    finally:
        db.close()


def run():
    logger.info("Ikobiz Scheduler started")
    while True:
        try:
            check_booking_reminders()
            check_scheduled_broadcasts()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        time.sleep(300)  # Every 5 minutes


if __name__ == "__main__":
    run()
