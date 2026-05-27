"""
app.py - Entry point for the Ikobiz FastAPI server.

Run with: uvicorn app:app --reload
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.shops import router as shops_router
from routers.products import router as products_router
from routers.ikobiz import router as ikobiz_router
from routers.negotiations import router as negotiations_router
from routers.whatsapp import router as whatsapp_router
from routers.dashboard import router as dashboard_router
from app.whatsapp.routes import router as whatsapp_bot_router

app = FastAPI(title="Ikobiz Marketplace API")

# Configure CORS for production and development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(shops_router)
app.include_router(products_router)
app.include_router(ikobiz_router)
app.include_router(negotiations_router)
app.include_router(whatsapp_router)
app.include_router(dashboard_router)
app.include_router(whatsapp_bot_router)


@app.get("/")
def root():
    return {"message": "Ikobiz API is running"}
