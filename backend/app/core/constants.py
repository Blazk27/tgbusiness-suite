"""
Application constants
"""

from enum import Enum


class UserRole(str, Enum):
    """User roles in the system"""
    OWNER = "owner"
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"


class AccountStatus(str, Enum):
    """Telegram account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    AUTH_REQUIRED = "auth_required"
    CONNECTION_ERROR = "connection_error"
    PENDING = "pending"


class ProxyStatus(str, Enum):
    """Proxy status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEAD = "dead"


class ProxyProtocol(str, Enum):
    """Proxy protocols"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class TaskType(str, Enum):
    """Automation task types"""
    PROFILE_PHOTO = "profile_photo"
    BIO_UPDATE = "bio_update"
    USERNAME_UPDATE = "username_update"
    MEDIA_SEND = "media_send"
    MESSAGE_SEND = "message_send"


class TaskStatus(str, Enum):
    """Automation task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubscriptionTier(str, Enum):
    """Subscription tiers"""
    STARTER = "starter"
    PRO = "pro"
    AGENCY = "agency"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    TRIALING = "trialing"


# Plan limits
PLAN_LIMITS = {
    "starter": {
        "max_accounts": 5,
        "max_users": 1,
        "max_automation_per_day": 100,
    },
    "pro": {
        "max_accounts": 50,
        "max_users": 5,
        "max_automation_per_day": 1000,
    },
    "agency": {
        "max_accounts": -1,  # Unlimited
        "max_users": -1,  # Unlimited
        "max_automation_per_day": -1,  # Unlimited
    },
}

# Plan prices (monthly)
PLAN_PRICES = {
    "starter": 29.00,
    "pro": 79.00,
    "agency": 199.00,
}

# Task type labels
TASK_TYPE_LABELS = {
    "profile_photo": "Profile Photo Upload",
    "bio_update": "Bio Update",
    "username_update": "Username Update",
    "media_send": "Media Send",
    "message_send": "Message Send",
}

# Automation settings
MIN_DELAY_SECONDS = 5
MAX_DELAY_SECONDS = 30
DEFAULT_DAILY_LIMIT = 20
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 60

# Rate limiting
DEFAULT_RATE_LIMIT = 100
DEFAULT_RATE_WINDOW = 60  # seconds
