"""
Global Exception Handler Middleware for ISP Framework.

Catches all unhandled exceptions and provides structured error responses.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.error_handling import ValidationError, error_handler


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and handle all unhandled exceptions."""

    async def dispatch(self, request: Request, call_next):
        """Process request and handle any exceptions."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Handle the exception using our error handler
            return await error_handler.handle_error(request, exc)


def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers for FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with structured error response."""
        return await error_handler.handle_error(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle request validation errors with structured response."""
        # Convert Pydantic validation error to our ValidationError
        error_details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field}: {error['msg']}")

        validation_error = ValidationError(
            detail=f"Validation failed: {'; '.join(error_details)}",
            context={
                "validation_errors": exc.errors(),
                "body": getattr(exc, "body", None),
            },
        )

        return await error_handler.handle_error(request, validation_error)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other unhandled exceptions."""
        return await error_handler.handle_error(request, exc)

    # Add the global exception middleware
    app.add_middleware(GlobalExceptionMiddleware)
