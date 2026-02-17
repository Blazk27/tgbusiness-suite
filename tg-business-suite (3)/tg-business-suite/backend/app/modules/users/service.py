"""
User service
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    ForbiddenException,
    ValidationException,
)
from app.core.constants import UserRole, PLAN_LIMITS
from app.modules.users.models import User
from app.modules.organizations.models import Organization
from app.core.security import generate_verification_token, get_password_hash


class UserService:
    """User service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_users_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get users by organization"""
        result = await self.db.execute(
            select(User)
            .where(User.organization_id == organization_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_users_by_organization(
        self,
        organization_id: UUID
    ) -> int:
        """Count users in organization"""
        result = await self.db.execute(
            select(func.count(User.id))
            .where(User.organization_id == organization_id)
        )
        return result.scalar() or 0

    async def invite_user(
        self,
        organization: Organization,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.STAFF
    ) -> User:
        """
        Invite a new user to the organization
        """
        # Check user limit
        user_count = await self.count_users_by_organization(organization.id)
        if user_count >= organization.max_users:
            raise ForbiddenException(
                f"User limit reached. Your plan allows {organization.max_users} users."
            )

        # Check if email already exists
        existing = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Email already registered")

        # Create user with temporary password
        temp_password = UserService._generate_temp_password()
        verification_token = generate_verification_token()

        user = User(
            organization_id=organization.id,
            email=email.lower(),
            hashed_password=get_password_hash(temp_password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_verified=False,
            verification_token=verification_token,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update_user(
        self,
        user: User,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Update user profile"""
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_role(
        self,
        target_user: User,
        new_role: UserRole,
        current_user: User
    ) -> User:
        """
        Update user role (only admin/owner can do this)
        """
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("Not authorized to change roles")

        # Owner cannot be demoted
        if target_user.role == UserRole.OWNER:
            raise ForbiddenException("Cannot change owner role")

        # Only owner can create other owners
        if new_role == UserRole.OWNER and current_user.role != UserRole.OWNER:
            raise ForbiddenException("Only owner can assign owner role")

        target_user.role = new_role
        await self.db.commit()
        await self.db.refresh(target_user)

        return target_user

    async def deactivate_user(
        self,
        target_user: User,
        current_user: User
    ) -> User:
        """Deactivate user account"""
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("Not authorized to deactivate users")

        # Cannot deactivate self
        if target_user.id == current_user.id:
            raise ValidationException("Cannot deactivate your own account")

        # Cannot deactivate owner
        if target_user.role == UserRole.OWNER:
            raise ForbiddenException("Cannot deactivate owner")

        target_user.is_active = False
        await self.db.commit()
        await self.db.refresh(target_user)

        return target_user

    async def reactivate_user(
        self,
        target_user: User,
        current_user: User
    ) -> User:
        """Reactivate user account"""
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("Not authorized to reactivate users")

        target_user.is_active = True
        await self.db.commit()
        await self.db.refresh(target_user)

        return target_user

    @staticmethod
    def _generate_temp_password() -> str:
        """Generate temporary password"""
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(16))
