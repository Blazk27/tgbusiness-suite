"""
Auth module
"""

from app.modules.auth.router import router
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    VerifyEmailRequest,
)

__all__ = [
    "router",
    "AuthService",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "VerifyEmailRequest",
]
