"""
Telegram Account model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.constants import AccountStatus


class TelegramAccount(Base):
    """Telegram account model"""

    __tablename__ = "telegram_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    phone_number = Column(String(20), nullable=False)
    session_encrypted = Column(Text, nullable=False)
    api_id = Column(Integer, nullable=False)
    api_hash = Column(String(255), nullable=False)
    proxy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("proxies.id", ondelete="SET NULL"),
        nullable=True
    )
    status = Column(
        SQLEnum(AccountStatus),
        default=AccountStatus.PENDING,
        nullable=False
    )
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    account_type = Column(String(50), default="user", nullable=False)
    daily_limit = Column(Integer, default=20, nullable=False)
    actions_today = Column(Integer, default=0, nullable=False)
    last_action_at = Column(DateTime, nullable=True)
    last_active = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    organization = relationship("Organization", back_populates="telegram_accounts")
    proxy = relationship("Proxy", back_populates="telegram_accounts")
    automation_tasks = relationship("AutomationTask", back_populates="account")

    def __repr__(self):
        return f"<TelegramAccount {self.phone_number} ({self.status})>"
