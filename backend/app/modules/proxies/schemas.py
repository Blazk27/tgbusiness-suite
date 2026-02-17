"""
Pydantic schemas for Proxies
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import ProxyStatus, ProxyProtocol


class ProxyBase(BaseModel):
    """Base proxy schema"""
    ip: str = Field(..., min_length=1, max_length=45)
    port: int = Field(..., ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: ProxyProtocol = ProxyProtocol.HTTP


class ProxyCreate(ProxyBase):
    """Proxy creation schema"""
    pass


class ProxyUpdate(BaseModel):
    """Proxy update schema"""
    ip: Optional[str] = Field(None, min_length=1, max_length=45)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: Optional[ProxyProtocol] = None
    status: Optional[ProxyStatus] = None


class ProxyResponse(ProxyBase):
    """Proxy response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    status: ProxyStatus
    latency: Optional[int]
    last_tested: Optional[datetime]
    created_at: datetime


class ProxyTestResult(BaseModel):
    """Proxy test result schema"""
    success: bool
    latency: Optional[int] = None
    error: Optional[str] = None
