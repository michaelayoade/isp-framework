"""
API Management Models

Models for comprehensive API management including:
- API Keys and authentication
- Rate limiting and quotas
- Usage analytics and monitoring
- API versioning and documentation
- Access control and permissions
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class APIKey(Base):
    """API Key management for external integrations"""
    __tablename__ = "api_management_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    api_secret = Column(String(255), nullable=False)
    
    # Ownership
    reseller_id = Column(Integer, ForeignKey("resellers.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)
    
    # Configuration
    permissions = Column(JSON, default=dict)  # Granular permissions
    scopes = Column(JSON, default=list)  # API scopes access
    rate_limit = Column(Integer, default=1000)  # requests per hour
    daily_quota = Column(Integer, default=10000)  # daily request limit
    monthly_quota = Column(Integer, default=100000)  # monthly request limit
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System-generated keys
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Security
    ip_whitelist = Column(JSON, default=list)  # Allowed IP addresses
    referrer_whitelist = Column(JSON, default=list)  # Allowed referrers
    user_agent_whitelist = Column(JSON, default=list)  # Allowed user agents
    
    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reseller = relationship("Reseller", back_populates="api_keys")
    customer = relationship("Customer", back_populates="api_keys")
    admin = relationship("Administrator", foreign_keys=[admin_id])
    creator = relationship("Administrator", foreign_keys=[created_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_api_keys_key', 'api_key'),
        Index('idx_api_keys_reseller', 'reseller_id'),
        Index('idx_api_keys_customer', 'customer_id'),
        Index('idx_api_keys_active', 'is_active'),
        Index('idx_api_keys_expires', 'expires_at'),
    )


class APIUsage(Base):
    """API usage tracking and analytics"""
    __tablename__ = "api_management_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_management_keys.id"), nullable=False)
    
    # Request details
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    status_code = Column(Integer, nullable=False)
    response_time = Column(Numeric(10, 3), nullable=False)  # milliseconds
    
    # Client information
    client_ip = Column(String(45))
    user_agent = Column(String(500))
    referrer = Column(String(500))
    
    # Request metadata
    request_size = Column(Integer, default=0)  # bytes
    response_size = Column(Integer, default=0)  # bytes
    
    # Error tracking
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_usage_key', 'api_key_id'),
        Index('idx_api_usage_endpoint', 'endpoint'),
        Index('idx_api_usage_method', 'method'),
        Index('idx_api_usage_status', 'status_code'),
        Index('idx_api_usage_date', 'created_at'),
        Index('idx_api_usage_error', 'error_type'),
    )


class APIRateLimit(Base):
    """Rate limiting tracking per API key"""
    __tablename__ = "api_management_rate_limit_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_management_keys.id"), nullable=False)
    
    # Time window tracking
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    
    # Usage counters
    request_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_key = relationship("APIKey", back_populates="rate_limits")
    
    # Indexes
    __table_args__ = (
        Index('idx_rate_limits_key_window', 'api_key_id', 'window_start', 'window_end'),
        Index('idx_rate_limits_active', 'api_key_id', 'window_end'),
    )


class APIVersion(Base):
    """API versioning and documentation"""
    __tablename__ = "api_management_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(20), unique=True, nullable=False)  # v1, v2, v1.1, etc.
    
    # Version details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    base_url = Column(String(500), nullable=False)
    
    # Status
    status = Column(String(20), default='active')  # active, deprecated, retired
    is_default = Column(Boolean, default=False)
    
    # Documentation
    documentation_url = Column(String(500))
    changelog = Column(Text)
    
    # Deprecation info
    deprecated_at = Column(DateTime(timezone=True), nullable=True)
    sunset_date = Column(DateTime(timezone=True), nullable=True)
    migration_guide = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_api_versions_version', 'version'),
        Index('idx_api_versions_status', 'status'),
        Index('idx_api_versions_default', 'is_default'),
    )


class APIEndpoint(Base):
    """API endpoint documentation and metadata"""
    __tablename__ = "api_endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    api_version_id = Column(Integer, ForeignKey("api_management_versions.id"), nullable=False)
    
    # Endpoint details
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, PATCH
    operation_id = Column(String(255), unique=True, nullable=False)
    
    # Documentation
    summary = Column(String(255))
    description = Column(Text)
    tags = Column(JSON, default=list)
    
    # Request/Response
    request_schema = Column(JSON)  # JSON Schema
    response_schema = Column(JSON)  # JSON Schema
    example_request = Column(JSON)
    example_response = Column(JSON)
    
    # Status and access
    is_deprecated = Column(Boolean, default=False)
    requires_auth = Column(Boolean, default=True)
    required_scopes = Column(JSON, default=list)
    
    # Performance
    average_response_time = Column(Numeric(10, 3), default=0)  # milliseconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_version = relationship("APIVersion", back_populates="endpoints")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_endpoints_version', 'api_version_id'),
        Index('idx_api_endpoints_path_method', 'path', 'method'),
        Index('idx_api_endpoints_operation', 'operation_id'),
        Index('idx_api_endpoints_deprecated', 'is_deprecated'),
    )


class APIQuota(Base):
    """API quota tracking and management"""
    __tablename__ = "api_management_quotas"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_management_keys.id"), nullable=False)
    
    # Quota period
    quota_type = Column(String(20), nullable=False)  # daily, monthly, custom
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Limits
    request_limit = Column(Integer, nullable=False)
    response_limit = Column(Integer, default=0)  # bytes
    
    # Usage tracking
    requests_used = Column(Integer, default=0)
    responses_sent = Column(Integer, default=0)  # bytes
    
    # Status
    is_exceeded = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api_key = relationship("APIKey", back_populates="quotas")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_quotas_key_period', 'api_key_id', 'period_start', 'period_end'),
        Index('idx_api_quotas_type', 'quota_type'),
        Index('idx_api_quotas_exceeded', 'is_exceeded'),
    )


# Add relationships to existing models
APIKey.usage_logs = relationship("APIUsage", back_populates="api_key", cascade="all, delete-orphan")
APIKey.rate_limits = relationship("APIRateLimit", back_populates="api_key", cascade="all, delete-orphan")
APIKey.quotas = relationship("APIQuota", back_populates="api_key", cascade="all, delete-orphan")

APIVersion.endpoints = relationship("APIEndpoint", back_populates="api_version", cascade="all, delete-orphan")
