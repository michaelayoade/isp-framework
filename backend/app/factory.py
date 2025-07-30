"""FastAPI App Factory for flexible initialization."""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

try:
    from app.core.config import settings
except Exception:
    # Fallback for testing environments
    class MockSettings:
        DEBUG = True
        ALLOWED_HOSTS = ["*"]
    settings = MockSettings()

from app.core.exceptions import add_exception_handlers

logger = logging.getLogger(__name__)


def create_app(include_optional_routers: bool = None) -> FastAPI:
    """
    Create FastAPI application with optional router inclusion.
    
    Args:
        include_optional_routers: If True, includes all routers including experimental ones.
                                 If False, only includes core routers.
                                 If None, uses ISP_FULL_IMPORT environment variable.
    """
    if include_optional_routers is None:
        include_optional_routers = os.getenv("ISP_FULL_IMPORT", "1").lower() in ("1", "true", "yes")
    
    app = FastAPI(
        title="ISP Framework API",
        description="Comprehensive ISP management platform",
        version="1.0.0",
        docs_url="/docs" if getattr(settings, 'DEBUG', True) else None,
        redoc_url="/redoc" if getattr(settings, 'DEBUG', True) else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if getattr(settings, 'DEBUG', True) else getattr(settings, 'ALLOWED_HOSTS', ['*']),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=getattr(settings, 'ALLOWED_HOSTS', ['*']) if not getattr(settings, 'DEBUG', True) else ["*"]
    )
    
    # Add exception handlers
    add_exception_handlers(app)
    
    # Import and register core routers (always available)
    try:
        from app.api.v1.endpoints import (
            auth, customers, billing, ticketing,
            administrators, resellers, settings as settings_router
        )
        
        # Core authentication and user management
        app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
        app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])
        app.include_router(administrators.router, prefix="/api/v1/administrators", tags=["administrators"])
        app.include_router(resellers.router, prefix="/api/v1/resellers", tags=["resellers"])
        
        # Core business functionality
        app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
        app.include_router(ticketing.router, prefix="/api/v1/tickets", tags=["ticketing"])
        app.include_router(settings_router.router, prefix="/api/v1/settings", tags=["settings"])
        
        logger.info("Core routers registered successfully")
        
    except ImportError as e:
        logger.warning(f"Some core routers could not be imported: {e}")
    
    # Import and register optional/experimental routers
    if include_optional_routers:
        try:
            from app.api.v1.endpoints import (
                internet_services, voice_services, bundle_services,
                network, devices, plugins, api_management,
                communications, file_storage, webhooks
            )
            
            # Service management routers
            app.include_router(internet_services.router, prefix="/api/v1/services/internet", tags=["internet-services"])
            app.include_router(voice_services.router, prefix="/api/v1/services/voice", tags=["voice-services"])
            app.include_router(bundle_services.router, prefix="/api/v1/services/bundles", tags=["bundle-services"])
            
            # Network and infrastructure
            app.include_router(network.router, prefix="/api/v1/network", tags=["network"])
            app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
            
            # Platform features
            app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["plugins"])
            app.include_router(api_management.router, prefix="/api/v1/api-management", tags=["api-management"])
            app.include_router(communications.router, prefix="/api/v1/communications", tags=["communications"])
            app.include_router(file_storage.router, prefix="/api/v1/files", tags=["file-storage"])
            app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
            
            logger.info("Optional routers registered successfully")
            
        except ImportError as e:
            logger.warning(f"Some optional routers could not be imported: {e}")
            logger.info("Application will continue with core functionality only")
    
    # Add health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for load balancers."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "optional_routers_enabled": include_optional_routers
        }
    
    # Add root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "ISP Framework API",
            "version": "1.0.0",
            "docs": "/docs" if getattr(settings, 'DEBUG', True) else "Contact administrator"
        }
    
    return app


def create_test_app() -> FastAPI:
    """Create FastAPI application for testing with minimal dependencies."""
    app = create_app(include_optional_routers=False)
    
    # Add observability endpoints for testing
    try:
        from app.core.observability import setup_observability
        setup_observability(app)
    except ImportError:
        # Add minimal health endpoint if observability module fails
        @app.get("/healthz")
        def health():
            return {"status": "healthy", "timestamp": "2025-01-01T00:00:00Z", "version": "test"}
    
    return app
