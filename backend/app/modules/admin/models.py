"""
Activity Log model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActivityLog(Base):
    """Activity log model for audit trail"""

    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog {self.action} on {self.resource_type}>"
