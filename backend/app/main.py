import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import create_tables
from app.core.exceptions import ISPFrameworkException
from app.core.observability import setup_observability
from app.core.security_middleware import setup_security_middleware
from app.middleware.exception_handler import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level), format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting ISP Framework API...")
    try:
        create_tables()
        logger.info("Database tables created/verified")

        # Initialize settings integration
        from app.core.config import initialize_settings_integration

        initialize_settings_integration()
        logger.info("Settings integration initialized")

        # Initialize enhanced audit system
        from app.core.audit_startup import audit_startup_event

        await audit_startup_event()
        logger.info("Enhanced audit system initialized")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ISP Framework API...")

    # Shutdown enhanced audit system
    from app.core.audit_startup import audit_shutdown_event

    await audit_shutdown_event()
    logger.info("Enhanced audit system shutdown completed")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)


# Exception handlers
@app.exception_handler(ISPFrameworkException)
async def isp_framework_exception_handler(request, exc: ISPFrameworkException):
    """Handle custom ISP Framework exceptions."""
    logger.error(f"ISP Framework exception: {exc.message} - Details: {exc.details}")
    return JSONResponse(
        status_code=400, content={"detail": exc.message, "extra": exc.details}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422, content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Database error occurred"})


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}!",
        "version": settings.app_version,
        "docs_url": settings.docs_url,
        "api_prefix": settings.api_v1_prefix,
    }


# Setup security middleware (rate limiting, headers, threat protection)
setup_security_middleware(app)

# Setup observability (metrics, logging, health checks)
setup_observability(app)

# Setup comprehensive error handling and alerting
setup_exception_handlers(app)

# Include API routers
app.include_router(api_router, prefix=settings.api_v1_prefix)
