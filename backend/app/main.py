"""
main.py - Unified FastAPI entry point for Ikobiz Platform.

Includes marketplace routers and the WhatsApp bot webhook.

Run with: uvicorn app.main:app --reload    (from backend/)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.shops import router as shops_router
from routers.products import router as products_router
from routers.dashboard import router as dashboard_router
from routers.cart import router as cart_router
from routers.messages import router as messages_router
from routers.upload import router as upload_router
from routers.bookings import router as bookings_router
from routers.broadcasts import router as broadcasts_router
from routers.payments import router as payments_router

# WhatsApp bot router
from app.whatsapp.routes import router as whatsapp_bot_router

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# ------------------------------------------------------------------
# App
# ------------------------------------------------------------------

app = FastAPI(title="Ikobiz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register marketplace routers
app.include_router(auth_router)
app.include_router(shops_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(messages_router)
app.include_router(upload_router)

# Register bookings, broadcast, and payment routers
app.include_router(bookings_router)
app.include_router(broadcasts_router)
app.include_router(payments_router)

# Register WhatsApp bot webhook
app.include_router(whatsapp_bot_router)


@app.get("/")
def root():
    return {"message": "Ikobiz API is running"}
