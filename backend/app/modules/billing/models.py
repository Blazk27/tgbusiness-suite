"""
Subscription Plan and Payment models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Boolean, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.constants import SubscriptionTier


class SubscriptionPlan(Base):
    """Subscription plan model"""

    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    stripe_price_id = Column(String(255), unique=True, nullable=False)
    stripe_product_id = Column(String(255), unique=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    interval = Column(String(20), nullable=False)  # monthly, yearly
    max_accounts = Column(Integer, nullable=False)
    max_users = Column(Integer, nullable=False)
    max_automation_per_day = Column(Integer, nullable=False)
    features = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    payments = relationship("Payment", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.name}>"


class Payment(Base):
    """Payment model"""

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    stripe_payment_id = Column(String(255), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd", nullable=False)
    status = Column(String(50), nullable=False)
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subscription_plans.id"),
        nullable=False
    )
    invoice_url = Column(Text, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="payments")
    plan = relationship("SubscriptionPlan", back_populates="payments")

    def __repr__(self):
        return f"<Payment {self.stripe_payment_id} ({self.status})>"
