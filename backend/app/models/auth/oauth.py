from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class OAuthClient(Base):
    """OAuth 2.0 client applications"""
    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), unique=True, index=True, nullable=False)
    client_secret = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    client_description = Column(Text)
    
    # Client configuration
    grant_types = Column(String(255), default="authorization_code,refresh_token")  # Comma-separated
    response_types = Column(String(255), default="code")  # Comma-separated
    scopes = Column(String(255), default="customer_portal,admin_portal,api")  # Comma-separated
    redirect_uris = Column(Text)  # JSON array as string
    
    # Security settings
    is_active = Column(Boolean, default=True)
    is_confidential = Column(Boolean, default=True)  # True for server-side apps, False for mobile/SPA
    token_endpoint_auth_method = Column(String(50), default="client_secret_basic")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tokens = relationship("OAuthToken", back_populates="client", cascade="all, delete-orphan")


class OAuthToken(Base):
    """OAuth 2.0 access and refresh tokens"""
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), ForeignKey("oauth_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("administrators.id"), nullable=True)  # Null for client_credentials
    
    # Token data
    access_token = Column(String(255), unique=True, index=True, nullable=False)
    refresh_token = Column(String(255), unique=True, index=True, nullable=True)
    token_type = Column(String(50), default="Bearer")
    scope = Column(String(255))  # Space-separated scopes
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    refresh_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Client IP and User Agent for security
    client_ip = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    # Relationships
    client = relationship("OAuthClient", back_populates="tokens")
    user = relationship("Administrator")


class OAuthAuthorizationCode(Base):
    """OAuth 2.0 authorization codes (for authorization_code flow)"""
    __tablename__ = "oauth_authorization_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(255), unique=True, index=True, nullable=False)
    client_id = Column(String(255), ForeignKey("oauth_clients.client_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    
    # Code data
    redirect_uri = Column(String(500), nullable=False)
    scope = Column(String(255))  # Space-separated scopes
    code_challenge = Column(String(255))  # For PKCE
    code_challenge_method = Column(String(10))  # S256 or plain
    
    # Expiration (authorization codes are short-lived, typically 10 minutes)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    client = relationship("OAuthClient")
    user = relationship("Administrator")
