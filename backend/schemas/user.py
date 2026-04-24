from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserRegister(BaseModel):
    """User registration request schema"""

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password 8-128 chars")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name 2-255 chars")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")

    @validator("password")
    def validate_password(cls, v):
        """Ensure password has uppercase, lowercase, and digit"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @validator("full_name")
    def validate_full_name(cls, v):
        """Ensure full name has no special characters"""
        if not all(c.isalnum() or c.isspace() for c in v):
            raise ValueError("Full name contains invalid characters")
        return v.strip()


class UserLogin(BaseModel):
    """User login request schema"""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """User response schema (no password)"""

    id: UUID
    email: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User profile update schema"""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)

    @validator("full_name")
    def validate_full_name(cls, v):
        if v is not None and not all(c.isalnum() or c.isspace() for c in v):
            raise ValueError("Full name contains invalid characters")
        return v.strip() if v else None


class TokenResponse(BaseModel):
    """Token response schema"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class OTPRequest(BaseModel):
    """OTP request schema"""

    email: EmailStr


class OTPVerify(BaseModel):
    """OTP verification schema"""

    email: EmailStr
    otp: str = Field(..., regex=r"^\d{6}$", description="6-digit OTP")
