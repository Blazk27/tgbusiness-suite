"""
Pydantic schemas for authentication
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.core.constants import UserRole


# Base schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=100)
    organization_name: str = Field(..., min_length=1, max_length=255)


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)


class UserResponse(UserBase):
    """User response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime


class UserInDB(UserResponse):
    """User in database schema"""
    hashed_password: str


# Organization schemas
class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)


class OrganizationCreate(OrganizationBase):
    """Organization creation schema"""
    pass


class OrganizationResponse(OrganizationBase):
    """Organization response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    subscription_tier: str
    subscription_status: str
    max_accounts: int
    max_users: int
    max_automation_per_day: int
    created_at: datetime


# Auth schemas
class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str


# Invitation schemas
class InviteUserRequest(BaseModel):
    """Invite user request schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.STAFF
