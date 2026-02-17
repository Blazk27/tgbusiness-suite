"""
Authentication service
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_verification_token,
    generate_password_reset_token,
)
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.constants import UserRole, PLAN_LIMITS, SubscriptionStatus
from app.modules.users.models import User
from app.modules.organizations.models import Organization

settings = get_settings()


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        organization_name: str
    ) -> Tuple[User, Organization]:
        """
        Register a new user with organization
        """
        # Validate password strength
        self._validate_password(password)

        # Check if email already exists
        existing_user = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        if existing_user.scalar_one_or_none():
            raise ConflictException("Email already registered")

        # Generate unique slug for organization
        slug = self._generate_slug(organization_name)
        slug = await self._ensure_unique_slug(slug)

        # Create organization with starter plan limits
        organization = Organization(
            name=organization_name,
            slug=slug,
            subscription_tier="starter",
            subscription_status=SubscriptionStatus.TRIALING,
            trial_end=datetime.utcnow() + timedelta(days=7),
            max_accounts=PLAN_LIMITS["starter"]["max_accounts"],
            max_users=PLAN_LIMITS["starter"]["max_users"],
            max_automation_per_day=PLAN_LIMITS["starter"]["max_automation_per_day"],
        )
        self.db.add(organization)
        await self.db.flush()

        # Generate verification token
        verification_token = generate_verification_token()

        # Create user as organization owner
        user = User(
            organization_id=organization.id,
            email=email.lower(),
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.OWNER,
            is_verified=False,  # Require email verification
            verification_token=verification_token,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(organization)
        await self.db.refresh(user)

        return user, organization

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and return tokens
        """
        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()

        # Generate tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "org_id": str(user.organization_id),
                "role": user.role.value
            }
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        return user, access_token, refresh_token

    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Tuple[str, str]:
        """
        Refresh access token using refresh token
        """
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedException("User not found or disabled")

        # Generate new tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "org_id": str(user.organization_id),
                "role": user.role.value
            }
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        return access_token, new_refresh_token

    async def verify_email(
        self,
        token: str
    ) -> User:
        """
        Verify user email
        """
        result = await self.db.execute(
            select(User).where(User.verification_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("Invalid verification token")

        if user.is_verified:
            raise ConflictException("Email already verified")

        user.is_verified = True
        user.verification_token = None
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def request_password_reset(
        self,
        email: str
    ) -> Optional[str]:
        """
        Request password reset token
        """
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()

        # Always return success to prevent email enumeration
        if not user:
            return None

        # Generate reset token
        reset_token = generate_password_reset_token()
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        await self.db.commit()

        return reset_token

    async def reset_password(
        self,
        token: str,
        new_password: str
    ) -> User:
        """
        Reset user password
        """
        self._validate_password(new_password)

        result = await self.db.execute(
            select(User).where(User.password_reset_token == token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException("Invalid reset token")

        if user.password_reset_expires < datetime.utcnow():
            raise UnauthorizedException("Reset token expired")

        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        await self.db.commit()
        await self.db.refresh(user)

        return user

    def _validate_password(self, password: str) -> None:
        """
        Validate password strength
        """
        if len(password) < 8:
            raise ValidationException("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", password):
            raise ValidationException(
                "Password must contain at least one uppercase letter"
            )

        if not re.search(r"[a-z]", password):
            raise ValidationException(
                "Password must contain at least one lowercase letter"
            )

        if not re.search(r"[0-9]", password):
            raise ValidationException(
                "Password must contain at least one number"
            )

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]

    async def _ensure_unique_slug(self, slug: str) -> str:
        """Ensure slug is unique"""
        result = await self.db.execute(
            select(Organization.slug).where(
                Organization.slug.like(f"{slug}%")
            )
        )
        existing_slugs = [row[0] for row in result.fetchall()]

        if slug not in existing_slugs:
            return slug

        # Add suffix to make unique
        counter = 1
        while f"{slug}-{counter}" in existing_slugs:
            counter += 1

        return f"{slug}-{counter}"
