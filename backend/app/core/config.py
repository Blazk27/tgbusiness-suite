"""
Core configuration module for TG Business Suite
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "TG Business Suite"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "your-secret-key-change-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://tguser:tgpass@localhost:5432/tgbusiness"
    postgres_user: str = "tguser"
    postgres_password: str = "tgpass"
    postgres_db: str = "tgbusiness"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Authentication
    jwt_secret_key: str = "your-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Session Encryption
    encryption_key: str = "your-32-byte-encryption-key-here"

    # Telegram
    telegram_api_id: Optional[int] = None
    telegram_api_hash: Optional[str] = None

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_publishable_key: Optional[str] = None

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Rate Limiting
    rate_limit_per_minute: int = 100
    login_rate_limit: int = 5
    login_rate_limit_window: int = 15  # minutes

    # File Upload
    max_file_size_mb: int = 100
    upload_dir: str = "/tmp/uploads"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Email (optional - for future implementation)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic"""
        return self.database_url.replace("+asyncpg", "").replace(
            "postgresql+asyncpg", "postgresql"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
