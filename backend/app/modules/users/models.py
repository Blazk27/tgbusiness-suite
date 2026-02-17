"""
User model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.constants import UserRole


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STAFF, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
    automation_tasks = relationship("AutomationTask", back_populates="user")
    media_uploads = relationship("MediaUpload", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
