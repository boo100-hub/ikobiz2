"""
config.py - WhatsApp-specific environment configuration.

Loads WhatsApp Cloud API credentials from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class WhatsAppSettings:
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    PHONE_NUMBER_ID: str = os.getenv("PHONE_NUMBER_ID", "")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "ikobiz_verify_123")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    API_VERSION: str = "v21.0"

    @property
    def GRAPH_API_URL(self) -> str:
        return f"https://graph.facebook.com/{self.API_VERSION}/{self.PHONE_NUMBER_ID}/messages"


whatsapp_settings = WhatsAppSettings()
