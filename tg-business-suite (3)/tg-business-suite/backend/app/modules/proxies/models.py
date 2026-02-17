"""
Proxy model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.constants import ProxyStatus, ProxyProtocol


class Proxy(Base):
    """Proxy model"""

    __tablename__ = "proxies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ip = Column(String(45), nullable=False)  # IPv6 can be up to 45 chars
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    protocol = Column(SQLEnum(ProxyProtocol), default=ProxyProtocol.HTTP, nullable=False)
    status = Column(SQLEnum(ProxyStatus), default=ProxyStatus.INACTIVE, nullable=False)
    latency = Column(Integer, nullable=True)  # Response time in ms
    last_tested = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    organization = relationship("Organization", back_populates="proxies")
    telegram_accounts = relationship("TelegramAccount", back_populates="proxy")

    def __repr__(self):
        return f"<Proxy {self.ip}:{self.port} ({self.protocol})>"

    @property
    def full_address(self) -> str:
        """Get full proxy address"""
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol.value}://{auth}{self.ip}:{self.port}"
