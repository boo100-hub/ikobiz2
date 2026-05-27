"""
config.py - Environment configuration for Ikobiz.

Loads settings from environment variables or .env file.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://ikobiz:ikobiz123@localhost:5432/ikobiz_db",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Frontend URL (used in notifications and links)
    SITE_URL: str = os.getenv("SITE_URL", "http://localhost:3000")

    # WhatsApp notification recipient override (for testing)
    NOTIFY_PHONE: str = os.getenv("NOTIFY_PHONE", "")


settings = Settings()
