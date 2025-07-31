"""
Observability infrastructure for ISP Framework.

Provides structured logging, metrics, tracing, and health checks.
"""

import time
import uuid
from datetime import datetime, timezone
from typing import Callable

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("isp.observability")

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes", "HTTP request size in bytes", ["method", "endpoint"]
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes", "HTTP response size in bytes", ["method", "endpoint"]
)

active_connections = Gauge("active_connections", "Number of active HTTP connections")

database_connections = Gauge(
    "database_connections_active", "Number of active database connections"
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging with metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Extract user context
        user_id = None
        client_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
        if hasattr(request.state, "client"):
            client_id = getattr(request.state.client, "client_id", None)

        # Get request size
        request_size = int(request.headers.get("content-length", 0))

        # Start timing
        start_time = time.time()
        active_connections.inc()

        # Process request
        try:
            response = await call_next(request)

            # Calculate metrics
            duration = time.time() - start_time
            response_size = int(response.headers.get("content-length", 0))

            # Extract endpoint pattern for metrics (remove path params)
            endpoint = self._get_endpoint_pattern(request)

            # Update Prometheus metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            if request_size > 0:
                http_request_size_bytes.labels(
                    method=request.method, endpoint=endpoint
                ).observe(request_size)

            if response_size > 0:
                http_response_size_bytes.labels(
                    method=request.method, endpoint=endpoint
                ).observe(response_size)

            # Structured logging
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "request_size_bytes": request_size,
                "response_size_bytes": response_size,
                "user_agent": request.headers.get("user-agent"),
                "remote_addr": request.client.host if request.client else None,
                "user_id": user_id,
                "client_id": client_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Log level based on status code
            if response.status_code >= 500:
                logger.error("HTTP request completed", **log_data)
            elif response.status_code >= 400:
                logger.warning("HTTP request completed", **log_data)
            else:
                logger.info("HTTP request completed", **log_data)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time
            endpoint = self._get_endpoint_pattern(request)

            # Update error metrics
            http_requests_total.labels(
                method=request.method, endpoint=endpoint, status_code=500
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method, endpoint=endpoint
            ).observe(duration)

            # Log error
            logger.error(
                "HTTP request failed",
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                user_id=user_id,
                client_id=client_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                exc_info=True,
            )

            raise
        finally:
            active_connections.dec()

    def _get_endpoint_pattern(self, request: Request) -> str:
        """Extract endpoint pattern for metrics (removes path parameters)."""
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path

        # Fallback: use path with basic parameter normalization
        path = request.url.path
        # Replace common ID patterns
        import re

        path = re.sub(r"/\d+", "/{id}", path)
        path = re.sub(r"/[a-f0-9-]{36}", "/{uuid}", path)
        return path


async def health_check() -> dict:
    """Basic health check - always returns OK."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": getattr(settings, "VERSION", "1.0.0"),
        "environment": getattr(settings, "ENVIRONMENT", "development"),
    }


async def readiness_check() -> dict:
    """Readiness check - validates external dependencies."""
    from app.core.database import engine
    
    checks = {}
    overall_status = "ready"

    # Database check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "message": "Connected"}
        database_connections.set(engine.pool.checkedout())
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "not_ready"

    # Redis check (if configured)
    if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
        try:
            import redis

            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            checks["redis"] = {"status": "healthy", "message": "Connected"}
        except Exception as e:
            checks["redis"] = {"status": "unhealthy", "message": str(e)}
            overall_status = "not_ready"

    # MinIO check (if configured)
    if hasattr(settings, "MINIO_ENDPOINT") and settings.MINIO_ENDPOINT:
        try:
            from minio import Minio

            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            # Simple check - list buckets
            list(client.list_buckets())
            checks["minio"] = {"status": "healthy", "message": "Connected"}
        except Exception as e:
            checks["minio"] = {"status": "unhealthy", "message": str(e)}
            overall_status = "not_ready"

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


def setup_observability(app: FastAPI) -> None:
    """Setup observability middleware and endpoints."""

    # Add request logging middleware
    if getattr(settings, "OBSERVABILITY_ENABLED", True):
        app.add_middleware(RequestLoggingMiddleware)
        logger.info("Request logging middleware enabled")

    # Health endpoints
    @app.get("/healthz", include_in_schema=False)
    async def health_z():
        """Health check endpoint."""
        return await health_check()

    # Backwards compatibility alias
    @app.get("/health", include_in_schema=False)
    async def health():
        """Health check alias for /healthz."""
        return await health_check()

    @app.get("/readyz", include_in_schema=False)
    async def readiness():
        """Readiness check endpoint."""
        result = await readiness_check()
        status_code = 200 if result["status"] == "ready" else 503
        return JSONResponse(content=result, status_code=status_code)

    # Metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    logger.info(
        "Observability endpoints configured",
        endpoints=["/healthz", "/readyz", "/metrics"],
    )


def get_audit_logger(domain: str) -> structlog.BoundLogger:
    """Get a domain-specific audit logger."""
    return structlog.get_logger(f"isp.audit.{domain}")


def log_audit_event(domain: str, event: str, **kwargs) -> None:
    """Log an audit event with structured data."""
    audit_logger = get_audit_logger(domain)
    audit_logger.info(
        event,
        audit_event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        **kwargs,
    )
