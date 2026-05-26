"""
ai_service.py - LLM-powered conversational reply via Groq API.

Falls back to None if GROQ_API_KEY is not configured,
so the caller can use rule-based replies instead.
"""

import logging
import httpx
from app.config import whatsapp_settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
TIMEOUT = 20.0

SYSTEM_PROMPT = """You are Ikobiz Assistant, a helpful WhatsApp chatbot for Ikobiz Marketplace — an African e-commerce platform where users can buy from shops or bid in a secondary market.

Your job is to help users discover products, find shops, and answer questions. Keep replies friendly, concise (under 400 characters), and use emojis.

Rules:
- Suggest relevant products or shops when users describe what they want
- Tell users to visit the website to complete purchases
- If asked something you can't answer, be honest and offer to connect them with a human
- Never invent pricing or stock information you're not sure about
- Always use KSh for prices
- The website URL is ikobiz.co.ke
- Shop links: ikobiz.co.ke/shops/{slug}
- Product links: ikobiz.co.ke/product/{id}
- Market listings: ikobiz.co.ke/market/{id}
"""


async def get_ai_reply(user_message: str, sender: str) -> str | None:
    """Send the user's message to Groq and return the AI reply."""
    key = whatsapp_settings.GROQ_API_KEY
    if not key:
        logger.info("GROQ_API_KEY not set — skipping AI reply")
        return None

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(GROQ_URL, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
            reply = data["choices"][0]["message"]["content"].strip()
            logger.info(f"AI reply to {sender}: {reply[:80]}...")
            return reply
    except httpx.HTTPStatusError as e:
        logger.error(f"Groq API error {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Groq request failed: {e}")
        return None
