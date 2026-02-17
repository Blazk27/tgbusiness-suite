"""
Core module - Application configuration, database, and security
"""

from app.core.config import get_settings, Settings
from app.core.database import get_db, get_db_session, Base, async_engine
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
    generate_password_reset_token,
    oauth2_scheme,
)
from app.core.encryption import encryption_service, SessionEncryptionService
from app.core.exceptions import (
    TGBusinessException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    ValidationException,
    RateLimitException,
    TelegramException,
    BillingException,
    SubscriptionLimitException,
)
from app.core.constants import (
    UserRole,
    AccountStatus,
    ProxyStatus,
    ProxyProtocol,
    TaskType,
    TaskStatus,
    SubscriptionTier,
    SubscriptionStatus,
    PLAN_LIMITS,
    PLAN_PRICES,
    TASK_TYPE_LABELS,
    MIN_DELAY_SECONDS,
    MAX_DELAY_SECONDS,
    DEFAULT_DAILY_LIMIT,
    MAX_RETRY_ATTEMPTS,
)

__all__ = [
    # Config
    "get_settings",
    "Settings",
    # Database
    "get_db",
    "get_db_session",
    "Base",
    "async_engine",
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_verification_token",
    "generate_password_reset_token",
    "oauth2_scheme",
    # Encryption
    "encryption_service",
    "SessionEncryptionService",
    # Exceptions
    "TGBusinessException",
    "UnauthorizedException",
    "ForbiddenException",
    "NotFoundException",
    "ConflictException",
    "ValidationException",
    "RateLimitException",
    "TelegramException",
    "BillingException",
    "SubscriptionLimitException",
    # Constants
    "UserRole",
    "AccountStatus",
    "ProxyStatus",
    "ProxyProtocol",
    "TaskType",
    "TaskStatus",
    "SubscriptionTier",
    "SubscriptionStatus",
    "PLAN_LIMITS",
    "PLAN_PRICES",
    "TASK_TYPE_LABELS",
    "MIN_DELAY_SECONDS",
    "MAX_DELAY_SECONDS",
    "DEFAULT_DAILY_LIMIT",
    "MAX_RETRY_ATTEMPTS",
]
