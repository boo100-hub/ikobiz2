"""
auth.py - Pydantic schemas for authentication requests and responses.
"""

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    phone: str | None = None
    is_seller: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    phone: str | None = None
    role: str

    model_config = {"from_attributes": True}
