"""
config.py - Environment configuration for Ikobiz.

Loads settings from environment variables or .env file.
"""

import os
from dotenv import load_dotenv
import re

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://ikobiz:ikobiz123@localhost:5432/ikobiz_db",
    )
    DEPLOYED_DB_URL: str = os.getenv(
        "DEPLOYED_DB_URL",
        "postgresql+psycopg://ikobiz:ikobiz123@localhost:5432/ikobiz_db",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Frontend URL (used in notifications and links)
    SITE_URL: str = os.getenv("SITE_URL", "http://localhost:3000")

    # WhatsApp notification recipient override (for testing)
    NOTIFY_PHONE: str = os.getenv("NOTIFY_PHONE", "")
    
    # WhatsApp webhook verification token
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "ikobiz_verify_123")

    # Cloudinary (for product image uploads)
    CLOUDINARY_URL: str = os.getenv("CLOUDINARY_URL", "")

    # M-Pesa Daraja API (Safaricom)
    MPESA_CONSUMER_KEY: str = os.getenv("MPESA_CONSUMER_KEY", "")
    MPESA_CONSUMER_SECRET: str = os.getenv("MPESA_CONSUMER_SECRET", "")
    MPESA_PASSKEY: str = os.getenv("MPESA_PASSKEY", "")
    MPESA_SHORTCODE: str = os.getenv("MPESA_SHORTCODE", "174379")       # Paybill/Till
    MPESA_ENV: str = os.getenv("MPESA_ENV", "sandbox")                   # "sandbox" | "production"
    MPESA_CALLBACK_URL: str = os.getenv(
        "MPESA_CALLBACK_URL",
        "https://your-domain.com/payments/mpesa-callback",
    )

    @property
    def cloudinary_config(self) -> dict:
        """Parse CLOUDINARY_URL into cloud_name / api_key / api_secret."""
        m = re.match(
            r"cloudinary://(\d+):([^@]+)@(.+)",
            self.CLOUDINARY_URL,
        )
        if not m:
            return {}
        return {
            "cloud_name": m.group(3),
            "api_key": m.group(1),
            "api_secret": m.group(2),
        }


settings = Settings()
