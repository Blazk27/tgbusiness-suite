"""
Billing service - Stripe integration
"""

from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.exceptions import NotFoundException, BillingException
from app.core.constants import (
    PLAN_LIMITS,
    SubscriptionStatus,
    SubscriptionTier,
)
from app.modules.billing.models import SubscriptionPlan, Payment
from app.modules.organizations.models import Organization

settings = get_settings()


class BillingService:
    """Billing service with Stripe integration"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_plans(self) -> List[SubscriptionPlan]:
        """Get all active subscription plans"""
        result = await self.db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.price)
        )
        return list(result.scalars().all())

    async def get_subscription(
        self,
        organization_id: UUID
    ) -> Dict:
        """Get organization subscription details"""
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = result.scalar_one_or_none()

        if not org:
            raise NotFoundException("Organization not found")

        tier = org.subscription_tier.value if hasattr(org.subscription_tier, 'value') else org.subscription_tier
        limits = PLAN_LIMITS.get(tier, PLAN_LIMITS["starter"])

        return {
            "tier": tier,
            "status": org.subscription_status.value if hasattr(org.subscription_status, 'value') else org.subscription_status,
            "current_period_start": None,
            "current_period_end": org.trial_end,
            "cancel_at_period_end": False,
            "trial_end": org.trial_end,
            "max_accounts": org.max_accounts,
            "max_users": org.max_users,
            "max_automation_per_day": org.max_automation_per_day,
        }

    async def create_subscription(
        self,
        organization_id: UUID,
        plan_id: str,
        payment_method_id: str
    ) -> Dict:
        """Create Stripe subscription"""
        # Get plan
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            raise NotFoundException("Plan not found")

        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = org_result.scalar_one_or_none()

        if not org:
            raise NotFoundException("Organization not found")

        # In production, this would create Stripe subscription
        # For now, we'll simulate the update
        tier = plan.name.lower()
        limits = PLAN_LIMITS.get(tier, PLAN_LIMITS["starter"])

        org.subscription_tier = tier
        org.subscription_status = SubscriptionStatus.ACTIVE
        org.max_accounts = limits["max_accounts"]
        org.max_users = limits["max_users"]
        org.max_automation_per_day = limits["max_automation_per_day"]

        await self.db.commit()

        return {
            "status": "subscription_created",
            "plan": plan.name,
        }

    async def get_portal_url(
        self,
        organization_id: UUID
    ) -> Dict:
        """Get Stripe customer portal URL"""
        # In production, create Stripe portal session
        # For now, return mock URL
        return {
            "url": "https://billing.stripe.com/p/session/test"
        }

    async def get_invoices(
        self,
        organization_id: UUID
    ) -> List[Payment]:
        """Get payment history"""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.organization_id == organization_id)
            .order_by(Payment.created_at.desc())
        )
        return list(result.scalars().all())

    async def handle_webhook(self, event: Dict) -> Dict:
        """Handle Stripe webhook events"""
        event_type = event.get("type")

        if event_type == "invoice.payment_succeeded":
            await self._handle_payment_succeeded(event)
        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(event)
        elif event_type == "customer.subscription.updated":
            await self._handle_subscription_updated(event)
        elif event_type == "customer.subscription.deleted":
            await self._handle_subscription_cancelled(event)

        return {"status": "processed"}

    async def _handle_payment_succeeded(self, event: Dict):
        """Handle successful payment"""
        # Update payment status
        pass

    async def _handle_payment_failed(self, event: Dict):
        """Handle failed payment"""
        # Mark subscription as past due
        pass

    async def _handle_subscription_updated(self, event: Dict):
        """Handle subscription update"""
        # Update subscription details
        pass

    async def _handle_subscription_cancelled(self, event: Dict):
        """Handle subscription cancellation"""
        # Update subscription status
        pass
