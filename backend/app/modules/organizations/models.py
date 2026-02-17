"""
Organization model - Multi-tenant support
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.constants import SubscriptionTier, SubscriptionStatus


class Organization(Base):
    """Organization model for multi-tenancy"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_tier = Column(
        SQLEnum(SubscriptionTier),
        default=SubscriptionTier.STARTER,
        nullable=False
    )
    subscription_status = Column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.TRIALING,
        nullable=False
    )
    trial_end = Column(DateTime, nullable=True)
    max_accounts = Column(Integer, default=5)
    max_users = Column(Integer, default=1)
    max_automation_per_day = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    telegram_accounts = relationship(
        "TelegramAccount",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    proxies = relationship("Proxy", back_populates="organization", cascade="all, delete-orphan")
    automation_tasks = relationship(
        "AutomationTask",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    media_uploads = relationship(
        "MediaUpload",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="organization", cascade="all, delete-orphan")
    activity_logs = relationship(
        "ActivityLog",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Organization {self.name} ({self.slug})>"
