"""
Proxies router
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.modules.auth.dependencies import get_current_verified_user, require_org_admin
from app.modules.users.models import User
from app.modules.proxies.schemas import (
    ProxyCreate,
    ProxyResponse,
    ProxyUpdate,
    ProxyTestResult,
)
from app.modules.proxies.service import ProxyService

router = APIRouter(prefix="/proxies", tags=["Proxies"])


@router.get("", response_model=List[ProxyResponse])
async def list_proxies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """List all proxies for the organization"""
    service = ProxyService(db)
    return await service.get_proxies(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=ProxyResponse, status_code=status.HTTP_201_CREATED)
async def add_proxy(
    data: ProxyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Add a new proxy"""
    service = ProxyService(db)
    return await service.create_proxy(
        organization_id=current_user.organization_id,
        ip=data.ip,
        port=data.port,
        username=data.username,
        password=data.password,
        protocol=data.protocol
    )


@router.get("/{proxy_id}", response_model=ProxyResponse)
async def get_proxy(
    proxy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Get proxy details"""
    service = ProxyService(db)
    return await service.get_proxy(proxy_id, current_user.organization_id)


@router.patch("/{proxy_id}", response_model=ProxyResponse)
async def update_proxy(
    proxy_id: UUID,
    data: ProxyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_org_admin)
):
    """Update proxy"""
    service = ProxyService(db)
    return await service.update_proxy(
        proxy_id,
        current_user.organization_id,
        data.model_dump(exclude_unset=True)
    )


@router.delete("/{proxy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proxy(
    proxy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_org_admin)
):
    """Delete proxy"""
    service = ProxyService(db)
    await service.delete_proxy(proxy_id, current_user.organization_id)


@router.post("/{proxy_id}/test", response_model=ProxyTestResult)
async def test_proxy(
    proxy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Test proxy connectivity"""
    service = ProxyService(db)
    return await service.test_proxy(proxy_id, current_user.organization_id)
