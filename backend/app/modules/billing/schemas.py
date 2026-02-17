"""
Pydantic schemas for Billing
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.core.constants import SubscriptionTier


class SubscriptionPlanBase(BaseModel):
    """Base subscription plan schema"""
    name: str
    price: Decimal = Field(..., ge=0)
    interval: str
    max_accounts: int
    max_users: int
    max_automation_per_day: int
    features: Dict[str, Any]


class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Subscription plan response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    stripe_price_id: str
    stripe_product_id: str
    is_active: bool
    created_at: datetime


class PaymentResponse(BaseModel):
    """Payment response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    stripe_payment_id: str
    amount: Decimal
    currency: str
    status: str
    plan_id: str
    invoice_url: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime


class SubscriptionResponse(BaseModel):
    """Subscription response schema"""
    tier: SubscriptionTier
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    trial_end: Optional[datetime]
    max_accounts: int
    max_users: int
    max_automation_per_day: int


class CreateSubscriptionRequest(BaseModel):
    """Create subscription request schema"""
    plan_id: str
    payment_method_id: str  # Stripe payment method ID


class SubscriptionUpgradeRequest(BaseModel):
    """Subscription upgrade request schema"""
    new_plan_id: str


class PortalResponse(BaseModel):
    """Customer portal response schema"""
    url: str


class InvoiceResponse(BaseModel):
    """Invoice response schema"""
    id: str
    number: str
    amount_due: Decimal
    amount_paid: Decimal
    status: str
    invoice_pdf: Optional[str]
    hosted_invoice_url: Optional[str]
    created: datetime
    due_date: Optional[datetime]
