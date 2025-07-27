from fastapi import HTTPException, status
from typing import Any, Dict, Optional


class ISPFrameworkException(Exception):
    """Base exception for ISP Framework."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ISPFrameworkException):
    """Raised when validation fails."""
    pass


class NotFoundError(ISPFrameworkException):
    """Raised when a resource is not found."""
    pass


class PermissionDeniedError(ISPFrameworkException):
    """Raised when user doesn't have permission."""
    pass


class DuplicateError(ISPFrameworkException):
    """Raised when trying to create a duplicate resource."""
    pass


class BusinessLogicError(ISPFrameworkException):
    """Raised when business logic validation fails."""
    pass


class RateLimitError(ISPFrameworkException):
    """Raised when rate limit is exceeded."""
    pass


class QuotaExceededError(ISPFrameworkException):
    """Raised when API quota is exceeded."""
    pass


# HTTP Exception creators
def create_not_found_exception(detail: str = "Resource not found") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail
    )


def create_validation_exception(detail: str = "Validation error") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail
    )


def create_permission_exception(detail: str = "Permission denied") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail
    )


def create_duplicate_exception(detail: str = "Resource already exists") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail
    )
