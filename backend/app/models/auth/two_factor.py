from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TwoFactorAuth(Base):
    """Two-Factor Authentication settings for administrators"""

    __tablename__ = "two_factor_auth"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(
        Integer, ForeignKey("administrators.id"), unique=True, nullable=False
    )

    # 2FA Configuration
    is_enabled = Column(Boolean, default=False)
    method = Column(String(20), default="totp")  # totp, sms, email
    secret_key = Column(String(255))  # TOTP secret key (encrypted)
    backup_codes = Column(Text)  # JSON array of backup codes (encrypted)

    # Phone/Email for SMS/Email 2FA
    phone_number = Column(String(20))  # For SMS 2FA
    email_address = Column(
        String(255)
    )  # For Email 2FA (can be different from admin email)

    # Status tracking
    verified_at = Column(DateTime(timezone=True))  # When 2FA was first verified
    last_used = Column(DateTime(timezone=True))  # Last successful 2FA verification
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(
        DateTime(timezone=True)
    )  # Temporary lock after failed attempts

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    administrator = relationship("Administrator", back_populates="two_factor_auth")


class TwoFactorBackupCode(Base):
    """Backup codes for 2FA recovery"""

    __tablename__ = "two_factor_backup_codes"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    code_hash = Column(String(255), nullable=False)  # Hashed backup code

    # Status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True))
    used_ip = Column(String(45))  # IP address where code was used

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    admin = relationship("Administrator")


class TwoFactorSession(Base):
    """Temporary sessions for 2FA verification"""

    __tablename__ = "two_factor_sessions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)

    # Session data
    client_ip = Column(String(45))
    user_agent = Column(Text)
    login_attempt_data = Column(Text)  # JSON data about the login attempt

    # Expiration (2FA sessions are short-lived, typically 5 minutes)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    admin = relationship("Administrator")


class ApiKey(Base):
    """API Keys for authentication"""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("administrators.id"), nullable=False)

    # Key identification
    key_name = Column(String(255), nullable=False)
    key_prefix = Column(
        String(20), nullable=False
    )  # First few chars for identification
    key_hash = Column(String(255), nullable=False)  # Hashed API key

    # Permissions and scope
    scopes = Column(String(500), default="api")  # Comma-separated scopes
    permissions = Column(Text)  # JSON permissions object

    # Security settings
    allowed_ips = Column(Text)  # JSON array of allowed IP addresses/ranges
    rate_limit = Column(Integer, default=1000)  # Requests per hour

    # Status and usage
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)

    # Expiration
    expires_at = Column(DateTime(timezone=True))  # Optional expiration

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    administrator = relationship("Administrator", back_populates="api_keys")


# Update Administrator model to include relationships
# This would be added to the Administrator model in base.py:
# two_factor_auth = relationship("TwoFactorAuth", back_populates="admin", uselist=False)
# api_keys = relationship("ApiKey", back_populates="admin")
