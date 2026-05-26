"""
main.py - Unified FastAPI entry point for Ikobiz Marketplace.

Includes marketplace routers and the WhatsApp bot webhook.

Run with: uvicorn app.main:app --reload    (from backend/)
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Marketplace routers
from routers.auth import router as auth_router
from routers.shops import router as shops_router
from routers.products import router as products_router
from routers.ikobiz import router as ikobiz_router
from routers.negotiations import router as negotiations_router
from routers.whatsapp import router as old_whatsapp_router
from routers.dashboard import router as dashboard_router
from routers.cart import router as cart_router

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

app = FastAPI(title="Ikobiz Marketplace API")

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
app.include_router(ikobiz_router)
app.include_router(negotiations_router)
app.include_router(old_whatsapp_router)
app.include_router(dashboard_router)
app.include_router(cart_router)

# Register WhatsApp bot webhook
app.include_router(whatsapp_bot_router)


@app.get("/")
def root():
    return {"message": "Ikobiz API is running"}
