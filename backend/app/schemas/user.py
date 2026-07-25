from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re


# ============ REQUEST SCHEMAS ============


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("full_name")
    def validate_full_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v.strip() if v else None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None

    @field_validator("full_name")
    def validate_full_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v.strip() if v else None


# ============ RESPONSE SCHEMAS ============


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    user: UserResponse
    token: TokenResponse


# ============ ERROR SCHEMAS ============


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
