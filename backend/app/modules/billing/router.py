"""
Billing router - Stripe integration
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import NotFoundException, BillingException
from app.modules.auth.dependencies import get_current_verified_user, require_org_owner
from app.modules.users.models import User
from app.modules.billing.schemas import (
    SubscriptionPlanResponse,
    SubscriptionResponse,
    PaymentResponse,
    CreateSubscriptionRequest,
    PortalResponse,
)
from app.modules.billing.service import BillingService

settings = get_settings()
router = APIRouter(prefix="/billing", tags=["Billing"])


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
):
    """List available subscription plans"""
    service = BillingService(db)
    return await service.get_plans()


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Get current subscription"""
    service = BillingService(db)
    return await service.get_subscription(current_user.organization_id)


@router.post("/subscribe", response_model=dict)
async def create_subscription(
    data: CreateSubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_org_owner)
):
    """Create new subscription"""
    service = BillingService(db)
    return await service.create_subscription(
        organization_id=current_user.organization_id,
        plan_id=data.plan_id,
        payment_method_id=data.payment_method_id
    )


@router.post("/portal", response_model=PortalResponse)
async def customer_portal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_org_owner)
):
    """Get Stripe customer portal URL"""
    service = BillingService(db)
    return await service.get_portal_url(current_user.organization_id)


@router.get("/invoices", response_model=List[PaymentResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """List payment history"""
    service = BillingService(db)
    return await service.get_invoices(current_user.organization_id)


@router.post("/webhook")
async def stripe_webhook(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhooks"""
    service = BillingService(db)
    return await service.handle_webhook(request)
