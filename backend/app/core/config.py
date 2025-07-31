from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Application
    app_name: str = "ISP Framework API"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://isp_user:Dotmac246@isp_postgres:5432/isp_framework"  # Docker network hostname
    database_echo: bool = False
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours
    refresh_token_expire_days: int = 7
    
    # Allowed hosts for Host header validation (TrustedHostMiddleware)
    allowed_hosts: List[str] = ["*"]

    # CORS
    allowed_origins: List[str] = ["*"]
    allowed_methods: List[str] = ["*"]
    allowed_headers: List[str] = ["*"]
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # File Storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "change_this_password"
    minio_secure: bool = False
    
    # API
    api_v1_prefix: str = "/api/v1"
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    
    # Pagination
    default_page_size: int = 25
    max_page_size: int = 100
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    
    # Portal ID System
    default_portal_prefix: str = "1000"
    portal_id_min_length: int = 5
    portal_id_max_length: int = 29
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file


# Global settings instance
settings = Settings()

# Settings integration flag
_settings_initialized = False

def initialize_settings_integration():
    """Initialize settings integration with the application."""
    global _settings_initialized
    if _settings_initialized:
        return
    
    try:
        # Import here to avoid circular imports
        from app.core.secrets_manager import initialize_secrets_from_env
        from app.services.settings_service import get_settings_service
        
        # Initialize secrets from environment
        initialize_secrets_from_env()
        
        # Initialize default settings in database
        with get_settings_service() as service:
            service.initialize_default_settings()
        
        _settings_initialized = True
        
    except Exception as e:
        # Don't fail startup if settings initialization fails
        import logging
        logging.warning(f"Settings initialization failed: {e}")

def get_runtime_setting(key: str, default=None):
    """Get a runtime setting from the database, fallback to config."""
    try:
        from app.services.settings_service import get_settings_service
        with get_settings_service() as service:
            return service.get_setting(key, default)
    except Exception:
        # Fallback to config or default
        return getattr(settings, key.lower().replace('.', '_'), default)
