"""Data source configuration model for external data integration."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.models.base import Base


class DataSourceConfig(Base):
    """
    Configuration for external data sources (APIs, SNMP, files, etc.).
    Enables dynamic integration of new data sources without code changes.
    """
    __tablename__ = "data_source_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Source identification
    source_name = Column(String(100), unique=True, nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # 'database', 'api', 'snmp', 'file', 'webhook'
    description = Column(Text)
    
    # Connection configuration (varies by source_type)
    connection_config = Column(JSONB, nullable=False)
    # Examples:
    # Database: {"host": "localhost", "database": "metrics", "table": "bandwidth_stats"}
    # API: {"base_url": "https://api.example.com", "auth_type": "bearer", "token_field": "access_token"}
    # SNMP: {"host": "192.168.1.1", "community": "public", "oids": ["1.3.6.1.2.1.2.2.1.10"]}
    # File: {"path": "/data/metrics", "format": "csv", "delimiter": ","}
    
    # Authentication and security
    auth_config = Column(JSONB)  # Separate auth configuration for security
    # Examples:
    # {"type": "basic", "username": "user", "password_env": "API_PASSWORD"}
    # {"type": "oauth2", "client_id": "xxx", "client_secret_env": "OAUTH_SECRET"}
    # {"type": "api_key", "key_field": "X-API-Key", "key_env": "EXTERNAL_API_KEY"}
    
    # Data processing
    data_mapping = Column(JSONB)  # Field mapping and transformations
    # Example: {"timestamp": "created_at", "value": "metric_value", "unit_conversion": "mbps_to_gbps"}
    
    # Refresh and caching
    refresh_interval_seconds = Column(Integer, default=300)  # 5 minutes
    timeout_seconds = Column(Integer, default=30)
    retry_attempts = Column(Integer, default=3)
    
    # Status and monitoring
    is_active = Column(Boolean, default=True, nullable=False)
    last_successful_fetch = Column(DateTime(timezone=True))
    last_error = Column(Text)
    error_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<DataSourceConfig(name='{self.source_name}', type='{self.source_type}')>"
