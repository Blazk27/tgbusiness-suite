"""
Authentication router
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
    RateLimitException,
)
from app.core.constants import PLAN_LIMITS, SubscriptionStatus
from app.modules.auth.schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    VerifyEmailRequest,
    InviteUserRequest,
)
from app.modules.auth.service import AuthService
from app.modules.auth.dependencies import (
    get_current_user,
    get_current_verified_user,
    require_org_owner,
    log_activity,
)
from app.modules.users.models import User
from app.modules.organizations.models import Organization
from app.modules.users.service import UserService

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Simple in-memory rate limiting (use Redis in production)
login_attempts = {}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Register a new user and organization
    """
    # Check rate limit
    client_ip = request.client.host if request else "unknown"
    await check_rate_limit(client_ip, "register")

    auth_service = AuthService(db)

    try:
        user, organization = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            organization_name=user_data.organization_name,
        )

        # Log activity
        await log_activity(
            db=db,
            user=user,
            action="register",
            resource_type="organization",
            resource_id=str(organization.id),
            request=request
        )

        return user

    except (ConflictException, ValidationException) as e:
        raise e


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Login and get access token
    """
    # Check rate limit
    client_ip = request.client.host if request else "unknown"
    await check_rate_limit(client_ip, "login", is_login=True)

    auth_service = AuthService(db)

    try:
        user, access_token, refresh_token = await auth_service.authenticate_user(
            email=form_data.username,
            password=form_data.password,
        )

        # Set refresh token in HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            expires=timedelta(days=settings.jwt_refresh_token_expire_days),
        )

        # Log activity
        await log_activity(
            db=db,
            user=user,
            action="login",
            resource_type="user",
            resource_id=str(user.id),
            request=request
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    except UnauthorizedException as e:
        # Track failed attempt
        track_failed_attempt(client_ip, "login")
        raise e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise UnauthorizedException("Refresh token not found")

    auth_service = AuthService(db)

    try:
        access_token, new_refresh_token = await auth_service.refresh_access_token(
            refresh_token
        )

        # Rotate refresh token
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            expires=timedelta(days=settings.jwt_refresh_token_expire_days),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )

    except UnauthorizedException as e:
        # Clear cookie on invalid token
        response.delete_cookie("refresh_token")
        raise e


@router.post("/logout")
async def logout(response: Response):
    """
    Logout and clear refresh token
    """
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.post("/verify-email")
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email address
    """
    auth_service = AuthService(db)
    user = await auth_service.verify_email(data.token)

    return {"message": "Email verified successfully", "user_id": str(user.id)}


@router.post("/forgot-password")
async def forgot_password(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email
    """
    auth_service = AuthService(db)
    await auth_service.request_password_reset(data.email)

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using token
    """
    auth_service = AuthService(db)
    user = await auth_service.reset_password(data.token, data.new_password)

    return {"message": "Password reset successfully", "user_id": str(user.id)}


async def check_rate_limit(
    client_ip: str,
    endpoint: str,
    is_login: bool = False
) -> None:
    """Check rate limit for endpoint"""
    key = f"{client_ip}:{endpoint}"

    if key not in login_attempts:
        login_attempts[key] = {"count": 0, "reset_time": None}

    attempt = login_attempts[key]

    # Reset counter if window expired
    if attempt["reset_time"] and datetime.now() > attempt["reset_time"]:
        attempt["count"] = 0
        attempt["reset_time"] = None

    max_attempts = settings.login_rate_limit if is_login else 10
    window = settings.login_rate_limit_window if is_login else 60

    if attempt["count"] >= max_attempts:
        raise RateLimitException(
            f"Too many attempts. Please try again in {window} minutes"
        )

    # Increment counter
    if is_login:
        attempt["count"] += 1
        if not attempt["reset_time"]:
            from datetime import datetime, timedelta
            attempt["reset_time"] = datetime.now() + timedelta(minutes=window)


def track_failed_attempt(client_ip: str, endpoint: str) -> None:
    """Track failed login attempt"""
    key = f"{client_ip}:{endpoint}"

    if key not in login_attempts:
        login_attempts[key] = {"count": 0, "reset_time": None}

    # Don't increment on failed attempt - only track
