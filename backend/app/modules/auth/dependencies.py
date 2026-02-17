"""
Authentication dependencies
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.constants import UserRole
from app.modules.users.models import User
from app.modules.organizations.models import Organization
from app.modules.admin.models import ActivityLog

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    if not token:
        raise UnauthorizedException("Authentication token required")

    payload = decode_token(token)
    user_id: str = payload.get("sub")
    org_id: str = payload.get("org_id")

    if user_id is None or org_id is None:
        raise UnauthorizedException("Invalid token payload")

    # Query user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled")

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify email is verified
    """
    if not current_user.is_verified:
        raise UnauthorizedException("Email not verified")

    return current_user


def require_role(*roles: UserRole):
    """
    Dependency factory for role-based access control
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException(
                f"Access denied. Required roles: {[r.value for r in roles]}"
            )
        return current_user

    return role_checker


async def require_org_owner(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require organization owner role"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenException("Only organization owner can perform this action")
    return current_user


async def require_org_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require organization admin or owner role"""
    if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise ForbiddenException("Only organization admin can perform this action")
    return current_user


async def log_activity(
    db: AsyncSession,
    user: User,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    request: Optional[Request] = None,
    metadata: Optional[dict] = None
) -> None:
    """
    Log user activity
    """
    ip_address = None
    user_agent = None

    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log = ActivityLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata
    )

    db.add(log)
    await db.commit()
