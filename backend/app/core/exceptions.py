"""
Custom exceptions for TG Business Suite
"""

from fastapi import HTTPException, status


class TGBusinessException(HTTPException):
    """Base exception for TG Business Suite"""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )


class UnauthorizedException(TGBusinessException):
    """Unauthorized access exception"""

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(TGBusinessException):
    """Forbidden access exception"""

    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(TGBusinessException):
    """Resource not found exception"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ConflictException(TGBusinessException):
    """Resource conflict exception"""

    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class ValidationException(TGBusinessException):
    """Validation error exception"""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class RateLimitException(TGBusinessException):
    """Rate limit exceeded exception"""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "60"}
        )


class TelegramException(TGBusinessException):
    """Telegram API exception"""

    def __init__(self, detail: str = "Telegram API error"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail
        )


class BillingException(TGBusinessException):
    """Billing related exception"""

    def __init__(self, detail: str = "Billing error"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail
        )


class SubscriptionLimitException(BillingException):
    """Subscription limit exceeded exception"""

    def __init__(self, detail: str = "Subscription limit exceeded"):
        super().__init__(detail=detail)
