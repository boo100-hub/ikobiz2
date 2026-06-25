"""
daraja.py - Safaricom M-Pesa Daraja API client.

Handles:
- OAuth token generation
- STK Push (Lipa Na M-Pesa Online)
- Payment query/status check
"""

import base64
import hashlib
import json
import logging
from datetime import datetime, timezone

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

BASE_URLS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}


def _get_base_url() -> str:
    return BASE_URLS.get(settings.MPESA_ENV, BASE_URLS["sandbox"])


def _generate_password() -> str:
    """Generate Lipa Na M-Pesa Online password."""
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode(), timestamp


def _get_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


async def get_oauth_token() -> str:
    """Get OAuth 2.0 token from Daraja API."""
    url = f"{_get_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    auth = base64.b64encode(
        f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"Basic {auth}"})
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"]


async def stk_push(
    phone: str,
    amount: float,
    account_ref: str,
    transaction_desc: str = "Ikobiz Payment",
) -> dict:
    """Initiate STK Push (Lipa Na M-Pesa Online) to customer phone.

    Args:
        phone: Customer phone in 254XXXXXXXXX format.
        amount: Amount to charge.
        account_ref: Order ID or reference shown on M-Pesa menu.
        transaction_desc: Description shown to customer.

    Returns:
        Raw Daraja API response dict.
    """
    token = await get_oauth_token()
    password, timestamp = _generate_password()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": round(amount),
        "PartyA": phone,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_ref[:12],  # Max 12 chars
        "TransactionDesc": transaction_desc[:13],  # Max 13 chars
    }

    url = f"{_get_base_url()}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def stk_query(checkout_request_id: str) -> dict:
    """Query the status of an STK Push transaction.

    Args:
        checkout_request_id: The CheckoutRequestID from stk_push response.

    Returns:
        Raw Daraja API response dict.
    """
    token = await get_oauth_token()
    password, timestamp = _generate_password()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    url = f"{_get_base_url()}/mpesa/stkpushquery/v1/query"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


def parse_callback(body: bytes | str) -> dict:
    """Parse Safaricom STK Push callback payload.

    Returns a normalized dict with keys:
        merchant_request_id, checkout_request_id, result_code, result_desc,
        amount, mpesa_receipt_number, transaction_date, phone_number
    """
    if isinstance(body, bytes):
        body = body.decode("utf-8")

    data = json.loads(body)
    stk = data.get("Body", {}).get("stkCallback", {})

    result = {
        "merchant_request_id": stk.get("MerchantRequestID"),
        "checkout_request_id": stk.get("CheckoutRequestID"),
        "result_code": stk.get("ResultCode"),
        "result_desc": stk.get("ResultDesc"),
        "amount": None,
        "mpesa_receipt_number": None,
        "transaction_date": None,
        "phone_number": None,
    }

    if stk.get("ResultCode") == 0:
        metadata = stk.get("CallbackMetadata", {}).get("Item", [])
        for item in metadata:
            name = item.get("Name")
            value = item.get("Value")
            if name == "Amount":
                result["amount"] = value
            elif name == "MpesaReceiptNumber":
                result["mpesa_receipt_number"] = value
            elif name == "TransactionDate":
                result["transaction_date"] = value
            elif name == "PhoneNumber":
                result["phone_number"] = value

    return result
