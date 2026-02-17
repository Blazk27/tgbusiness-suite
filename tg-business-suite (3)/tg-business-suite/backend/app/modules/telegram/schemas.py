"""
Pydantic schemas for Telegram accounts
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import AccountStatus


class TelegramAccountBase(BaseModel):
    """Base Telegram account schema"""
    phone_number: str = Field(..., min_length=5, max_length=20)
    api_id: int = Field(..., gt=0)
    api_hash: str = Field(..., min_length=32, max_length=64)
    proxy_id: Optional[str] = None
    daily_limit: int = Field(default=20, ge=1, le=100)


class TelegramAccountCreate(TelegramAccountBase):
    """Telegram account creation schema"""
    session_file: bytes = Field(..., description="Session file content")


class TelegramAccountUpdate(BaseModel):
    """Telegram account update schema"""
    proxy_id: Optional[str] = None
    daily_limit: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[AccountStatus] = None


class TelegramAccountResponse(TelegramAccountBase):
    """Telegram account response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    status: AccountStatus
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    account_type: str
    actions_today: int
    last_action_at: Optional[datetime]
    last_active: Optional[datetime]
    created_at: datetime


class TelegramAccountConnect(BaseModel):
    """Telegram account connection schema"""
    session_file: bytes


class TelegramAccountStatus(BaseModel):
    """Telegram account status schema"""
    status: AccountStatus
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_premium: Optional[bool] = None
    last_active: Optional[datetime] = None
