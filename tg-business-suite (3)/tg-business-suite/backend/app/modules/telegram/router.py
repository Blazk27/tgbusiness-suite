"""
Telegram accounts router
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ForbiddenException
from app.modules.auth.dependencies import (
    get_current_verified_user,
    require_org_admin,
)
from app.modules.users.models import User
from app.modules.telegram.schemas import (
    TelegramAccountResponse,
    TelegramAccountCreate,
    TelegramAccountUpdate,
    TelegramAccountStatus,
)
from app.modules.telegram.service import telegram_service

router = APIRouter(prefix="/accounts", tags=["Telegram Accounts"])


@router.get("", response_model=List[TelegramAccountResponse])
async def list_accounts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """List all Telegram accounts for the organization"""
    from sqlalchemy import select
    from app.modules.telegram.models import TelegramAccount

    result = await db.execute(
        select(TelegramAccount)
        .where(TelegramAccount.organization_id == current_user.organization_id)
        .offset(skip)
        .limit(limit)
    )
    accounts = result.scalars().all()

    return accounts


@router.post("", response_model=TelegramAccountResponse, status_code=status.HTTP_201_CREATED)
async def add_account(
    phone_number: str = Form(...),
    api_id: int = Form(...),
    api_hash: str = Form(...),
    proxy_id: Optional[str] = Form(None),
    daily_limit: int = Form(20),
    session_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
    request = None
):
    """Add a new Telegram account"""
    from app.modules.telegram.models import TelegramAccount
    from app.core.constants import AccountStatus

    # Read session file
    session_data = await session_file.read()

    if len(session_data) > 50 * 1024 * 1024:  # 50MB max
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Session file too large"
        )

    # Convert proxy_id
    proxy_uuid = UUID(proxy_id) if proxy_id else None

    try:
        account = await telegram_service.add_account(
            db=db,
            phone_number=phone_number,
            session_data=session_data,
            api_id=api_id,
            api_hash=api_hash,
            proxy_id=proxy_uuid,
            daily_limit=daily_limit
        )

        # Log activity
        from app.modules.auth.dependencies import log_activity
        await log_activity(
            db=db,
            user=current_user,
            action="add_account",
            resource_type="telegram_account",
            resource_id=str(account.id),
            request=request
        )

        return account

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{account_id}", response_model=TelegramAccountResponse)
async def get_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Get Telegram account details"""
    from sqlalchemy import select
    from app.modules.telegram.models import TelegramAccount

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.organization_id == current_user.organization_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise NotFoundException("Account not found")

    return account


@router.patch("/{account_id}", response_model=TelegramAccountResponse)
async def update_account(
    account_id: UUID,
    data: TelegramAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Update Telegram account"""
    from sqlalchemy import select
    from app.modules.telegram.models import TelegramAccount

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.organization_id == current_user.organization_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise NotFoundException("Account not found")

    if data.proxy_id is not None:
        account.proxy_id = UUID(data.proxy_id) if data.proxy_id else None

    if data.daily_limit is not None:
        account.daily_limit = data.daily_limit

    if data.status is not None:
        account.status = data.status

    await db.commit()
    await db.refresh(account)

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_org_admin),
    request = None
):
    """Delete Telegram account"""
    from sqlalchemy import select, delete
    from app.modules.telegram.models import TelegramAccount

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.organization_id == current_user.organization_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise NotFoundException("Account not found")

    # Disconnect first
    await telegram_service.disconnect_account(db, account_id)

    # Delete from database
    await db.delete(account)
    await db.commit()

    # Log activity
    from app.modules.auth.dependencies import log_activity
    await log_activity(
        db=db,
        user=current_user,
        action="delete_account",
        resource_type="telegram_account",
        resource_id=str(account_id),
        request=request
    )


@router.post("/{account_id}/connect", response_model=TelegramAccountStatus)
async def connect_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Connect to Telegram account"""
    from sqlalchemy import select
    from app.modules.telegram.models import TelegramAccount

    # Verify ownership
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.organization_id == current_user.organization_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise NotFoundException("Account not found")

    try:
        result = await telegram_service.connect_account(db, account_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{account_id}/disconnect")
async def disconnect_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Disconnect from Telegram account"""
    from sqlalchemy import select
    from app.modules.telegram.models import TelegramAccount

    # Verify ownership
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.organization_id == current_user.organization_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise NotFoundException("Account not found")

    await telegram_service.disconnect_account(db, account_id)

    return {"message": "Account disconnected"}


@router.get("/{account_id}/status", response_model=TelegramAccountStatus)
async def check_account_status(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Check account connection status"""
    from sqlalchemy import select
    from app.modules.telegram.models import TelegramAccount

    # Verify ownership
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.organization_id == current_user.organization_id
        )
    )
    account = result.scalar_one_or_none()

    if not account:
        raise NotFoundException("Account not found")

    return await telegram_service.check_account_status(db, account_id)
