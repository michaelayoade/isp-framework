"""
Base Authentication Models

Core authentication models including Administrator and user management.
"""

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Administrator(Base):
    """Administrator user model for system access and management"""

    __tablename__ = "administrators"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(50), nullable=False, default="admin")
    permissions = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships (defined as strings to avoid circular imports)
    two_factor_auth = relationship(
        "TwoFactorAuth", back_populates="administrator", uselist=False
    )
    api_keys = relationship("ApiKey", back_populates="administrator")
    # RBAC relationships
    user_roles = relationship(
        "UserRole", foreign_keys="UserRole.user_id", back_populates="user"
    )
