"""
Error Handling & Alerting System for ISP Framework.

Provides global exception handling, error categorization, and alerting integration.
"""

import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.observability import get_audit_logger


# Error severity levels
class ErrorSeverity(str, Enum):
    """Error severity classification for alerting and escalation."""

    CRITICAL = "critical"  # System down, customer impact, immediate response
    HIGH = "high"  # Service degradation, SLA impact, urgent response
    MEDIUM = "medium"  # Feature issues, minor impact, standard response
    LOW = "low"  # Warnings, informational, routine response


# Error categories for ISP operations
class ErrorCategory(str, Enum):
    """Error categories specific to ISP operations."""

    AUTHENTICATION = "authentication"  # Login, token, permission errors
    BILLING = "billing"  # Payment, invoice, accounting errors
    CUSTOMER = "customer"  # Customer management errors
    NETWORK = "network"  # Network device, connectivity errors
    SERVICE = "service"  # Service provisioning, management errors
    RADIUS = "radius"  # RADIUS authentication, session errors
    DATABASE = "database"  # Database connection, query errors
    INTEGRATION = "integration"  # External API, webhook errors
    VALIDATION = "validation"  # Input validation, schema errors
    SYSTEM = "system"  # Internal system, infrastructure errors


# Error impact levels for customer assessment
class ErrorImpact(str, Enum):
    """Customer impact assessment for error prioritization."""

    CUSTOMER_FACING = "customer_facing"  # Direct customer service impact
    OPERATIONAL = "operational"  # Internal operations impact
    ADMINISTRATIVE = "administrative"  # Admin/staff workflow impact
    MONITORING = "monitoring"  # Monitoring/reporting impact


class ErrorDetail(BaseModel):
    """Structured error detail following RFC 7807 Problem Details."""

    type: str  # Error type URI
    title: str  # Human-readable summary
    status: int  # HTTP status code
    detail: str  # Human-readable explanation
    instance: str  # URI reference to specific occurrence
    error_id: str  # Unique error identifier
    timestamp: datetime  # Error occurrence timestamp
    severity: ErrorSeverity  # Error severity level
    category: ErrorCategory  # Error category
    impact: ErrorImpact  # Customer impact level
    context: Dict[str, Any] = {}  # Additional context data
    stack_trace: Optional[str] = None  # Stack trace for debugging
    user_id: Optional[str] = None  # User associated with error
    customer_id: Optional[int] = None  # Customer associated with error
    correlation_id: Optional[str] = None  # Request correlation ID

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ISPException(Exception):
    """Base exception class for ISP Framework with structured error details."""

    def __init__(
        self,
        title: str,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        impact: ErrorImpact = ErrorImpact.OPERATIONAL,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        customer_id: Optional[int] = None,
    ):
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.severity = severity
        self.category = category
        self.impact = impact
        self.context = context or {}
        self.user_id = user_id
        self.customer_id = customer_id
        super().__init__(detail)


# Specific ISP exception classes
class AuthenticationError(ISPException):
    """Authentication and authorization errors."""

    def __init__(self, detail: str, **kwargs):
        super().__init__(
            title="Authentication Error",
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            impact=ErrorImpact.CUSTOMER_FACING,
            **kwargs,
        )


class BillingError(ISPException):
    """Billing and payment processing errors."""

    def __init__(self, detail: str, **kwargs):
        super().__init__(
            title="Billing Error",
            detail=detail,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.BILLING,
            impact=ErrorImpact.CUSTOMER_FACING,
            **kwargs,
        )


class NetworkError(ISPException):
    """Network infrastructure and device errors."""

    def __init__(self, detail: str, **kwargs):
        super().__init__(
            title="Network Error",
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.NETWORK,
            impact=ErrorImpact.CUSTOMER_FACING,
            **kwargs,
        )


class ServiceProvisioningError(ISPException):
    """Service provisioning and management errors."""

    def __init__(self, detail: str, **kwargs):
        super().__init__(
            title="Service Provisioning Error",
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SERVICE,
            impact=ErrorImpact.CUSTOMER_FACING,
            **kwargs,
        )


class RADIUSError(ISPException):
    """RADIUS authentication and session errors."""

    def __init__(self, detail: str, **kwargs):
        super().__init__(
            title="RADIUS Error",
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.RADIUS,
            impact=ErrorImpact.CUSTOMER_FACING,
            **kwargs,
        )


class ValidationError(ISPException):
    """Input validation and schema errors."""

    def __init__(self, detail: str, **kwargs):
        super().__init__(
            title="Validation Error",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            impact=ErrorImpact.OPERATIONAL,
            **kwargs,
        )


class ErrorHandler:
    """Global error handler with structured logging and alerting."""

    def __init__(self):
        self.logger = structlog.get_logger("isp.error_handler")
        self.audit_logger = get_audit_logger("error_handling")

    def create_error_detail(
        self,
        exception: Exception,
        request: Optional[Request] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> ErrorDetail:
        """Create structured error detail from exception."""
        error_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)

        # Extract correlation ID from request headers
        correlation_id = None
        if request and hasattr(request.state, "correlation_id"):
            correlation_id = request.state.correlation_id

        # Handle ISP-specific exceptions
        if isinstance(exception, ISPException):
            return ErrorDetail(
                type=f"https://ispframework.com/errors/{exception.category.value}",
                title=exception.title,
                status=exception.status_code,
                detail=exception.detail,
                instance=f"/errors/{error_id}",
                error_id=error_id,
                timestamp=timestamp,
                severity=exception.severity,
                category=exception.category,
                impact=exception.impact,
                context=exception.context,
                stack_trace=traceback.format_exc(),
                user_id=exception.user_id,
                customer_id=exception.customer_id,
                correlation_id=correlation_id,
            )

        # Handle FastAPI HTTP exceptions
        elif isinstance(exception, HTTPException):
            severity = self._determine_severity_from_status(exception.status_code)
            category = self._determine_category_from_status(exception.status_code)

            return ErrorDetail(
                type="https://ispframework.com/errors/http",
                title="HTTP Error",
                status=exception.status_code,
                detail=str(exception.detail),
                instance=f"/errors/{error_id}",
                error_id=error_id,
                timestamp=timestamp,
                severity=severity,
                category=category,
                impact=ErrorImpact.OPERATIONAL,
                stack_trace=traceback.format_exc(),
                correlation_id=correlation_id,
            )

        # Handle generic exceptions
        else:
            return ErrorDetail(
                type="https://ispframework.com/errors/system",
                title="Internal Server Error",
                status=status_code,
                detail=str(exception),
                instance=f"/errors/{error_id}",
                error_id=error_id,
                timestamp=timestamp,
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.SYSTEM,
                impact=ErrorImpact.OPERATIONAL,
                stack_trace=traceback.format_exc(),
                correlation_id=correlation_id,
            )

    def _determine_severity_from_status(self, status_code: int) -> ErrorSeverity:
        """Determine error severity from HTTP status code."""
        if status_code >= 500:
            return ErrorSeverity.CRITICAL
        elif status_code >= 400:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _determine_category_from_status(self, status_code: int) -> ErrorCategory:
        """Determine error category from HTTP status code."""
        if status_code == 401:
            return ErrorCategory.AUTHENTICATION
        elif status_code == 402:
            return ErrorCategory.BILLING
        elif status_code == 422:
            return ErrorCategory.VALIDATION
        elif status_code >= 500:
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.SYSTEM

    async def handle_error(
        self, request: Request, exception: Exception
    ) -> JSONResponse:
        """Handle error with logging, alerting, and structured response."""
        error_detail = self.create_error_detail(exception, request)

        # Log structured error
        self.logger.error(
            "Error occurred",
            error_id=error_detail.error_id,
            error_type=error_detail.type,
            title=error_detail.title,
            status=error_detail.status,
            severity=error_detail.severity.value,
            category=error_detail.category.value,
            impact=error_detail.impact.value,
            user_id=error_detail.user_id,
            customer_id=error_detail.customer_id,
            correlation_id=error_detail.correlation_id,
            context=error_detail.context,
            path=str(request.url) if request else None,
            method=request.method if request else None,
        )

        # Log audit event for high-severity errors
        if error_detail.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self.audit_logger.warning(
                "High-severity error occurred",
                error_id=error_detail.error_id,
                severity=error_detail.severity.value,
                category=error_detail.category.value,
                impact=error_detail.impact.value,
                detail=error_detail.detail,
            )

        # Trigger alerting for critical errors
        if error_detail.severity == ErrorSeverity.CRITICAL:
            await self._trigger_alert(error_detail, request)

        # Return structured error response
        response_data = error_detail.dict(exclude={"stack_trace"})

        # Convert datetime objects to ISO format strings for JSON serialization
        if "timestamp" in response_data and hasattr(
            response_data["timestamp"], "isoformat"
        ):
            response_data["timestamp"] = response_data["timestamp"].isoformat()

        # Include stack trace in development mode
        from app.core.config import settings

        if settings.debug:
            response_data["stack_trace"] = error_detail.stack_trace

        return JSONResponse(
            status_code=error_detail.status,
            content=response_data,
            headers={
                "Content-Type": "application/problem+json",
                "X-Error-ID": error_detail.error_id,
            },
        )

    async def _trigger_alert(
        self, error_detail: ErrorDetail, request: Optional[Request]
    ):
        """Trigger alerting for critical errors via Grafana alert manager."""
        try:
            # Import here to avoid circular imports
            from app.core.alerting import grafana_alert_manager

            # Process error through Grafana alert manager
            await grafana_alert_manager.process_error(error_detail)

            self.logger.info(
                "Alert triggered via Grafana alert manager",
                error_id=error_detail.error_id,
                severity=error_detail.severity.value,
                category=error_detail.category.value,
                impact=error_detail.impact.value,
            )

        except Exception as alert_error:
            # Fallback logging if alerting fails
            self.logger.critical(
                "ALERT: Critical error requires immediate attention (alerting failed)",
                error_id=error_detail.error_id,
                title=error_detail.title,
                detail=error_detail.detail,
                category=error_detail.category.value,
                impact=error_detail.impact.value,
                customer_id=error_detail.customer_id,
                path=str(request.url) if request else None,
                alert_error=str(alert_error),
            )


# Global error handler instance
error_handler = ErrorHandler()
