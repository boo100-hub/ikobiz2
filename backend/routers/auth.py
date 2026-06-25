"""
routers/auth.py - Registration, login, and current-user endpoints.

POST /auth/register          - create a new user account
POST /auth/login             - obtain a JWT token
POST /auth/otp/request       - request OTP for phone login
POST /auth/otp/verify        - verify OTP and return JWT
GET  /auth/me                - return the authenticated user's profile
POST /auth/link-whatsapp     - link current web account to WhatsApp phone
"""

import logging
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import hash_password, verify_password, create_access_token
from dependencies.auth import get_current_user
from models import User
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut, OtpRequest, OtpVerifyRequest, LinkWhatsAppRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory OTP store (phone -> {"code": str, "expires": float})
_otp_store: dict[str, dict] = {}
_OTP_EXPIRY_SECONDS = 300  # 5 minutes


def _generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)  # 6-digit OTP


@router.post("/otp/request")
def request_otp(data: OtpRequest, db: Session = Depends(get_db)):
    """Request an OTP for phone-based login. If the phone exists, send OTP via WhatsApp."""
    phone = data.phone.strip().replace("+", "").replace(" ", "")
    code = _generate_otp()
    _otp_store[phone] = {"code": code, "expires": time.time() + _OTP_EXPIRY_SECONDS}
    logger.info(f"OTP for {phone}: {code}")

    # Try to send OTP via WhatsApp if the user exists and has a WhatsApp session
    user = db.query(User).filter(User.phone == phone).first()
    try:
        from app.whatsapp.service import send_text_message_sync
        send_text_message_sync(
            phone,
            f"🔐 *Ikobiz Login Code*\n\nYour verification code is:\n\n*{code}*\n\n"
            f"This code expires in 5 minutes. Do not share it.\n\n"
            f"If you didn't request this, ignore this message.",
        )
    except Exception:
        logger.info(f"Could not send WhatsApp OTP to {phone}, SMS fallback needed")

    return {"message": "OTP sent to your phone", "phone": phone}


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(data: OtpVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and return JWT token. Creates account if phone doesn't exist."""
    phone = data.phone.strip().replace("+", "").replace(" ", "")
    otp_data = _otp_store.get(phone)

    if not otp_data:
        raise HTTPException(status_code=400, detail="No OTP requested for this phone number")
    if time.time() > otp_data["expires"]:
        _otp_store.pop(phone, None)
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one")
    if otp_data["code"] != data.code.strip():
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    _otp_store.pop(phone, None)

    # Find or create user
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        username = f"wa_{phone}"
        email = f"{phone}@whatsapp.ikobiz.com"
        attempt = 0
        while db.query(User).filter(User.username == username).first():
            attempt += 1
            username = f"wa_{phone}_{attempt}"
        while db.query(User).filter(User.email == email).first():
            email = f"{phone}_{attempt}@whatsapp.ikobiz.com"

        user = User(
            username=username,
            email=email,
            phone=phone,
            password_hash=hash_password(secrets.token_urlsafe(16)),
            role="buyer",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created user via OTP: {username} ({phone})")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/link-whatsapp")
def link_whatsapp(data: LinkWhatsAppRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Link the current web account to a WhatsApp phone number via OTP verification."""
    phone = data.phone.strip().replace("+", "").replace(" ", "")

    # Verify OTP was just validated (re-use the same store)
    otp_data = _otp_store.get(phone)
    if not otp_data or otp_data.get("verified") is not True:
        raise HTTPException(status_code=400, detail="Please verify the phone number via OTP first")

    existing = db.query(User).filter(User.phone == phone, User.id != user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone already linked to another account")

    user.phone = phone
    db.commit()
    _otp_store.pop(phone, None)
    return {"message": "WhatsApp number linked successfully", "phone": phone}


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user account and return the user profile."""
    # Check for existing username / email
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=data.username,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role="seller" if data.is_seller else "buyer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with username or email + password and receive a JWT."""
    logger.info(f"Login attempt for: {data.username}")
    # Try username first, then email
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        user = db.query(User).filter(User.email == data.username).first()
    
    if not user:
        logger.warning(f"User not found: {data.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not verify_password(data.password, user.password_hash):
        logger.warning(f"Invalid password for user: {data.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    logger.info(f"Login successful for user: {user.username}")
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return user
