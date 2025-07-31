from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.models.foundation.base import Base


class Role(Base):
    """Role lookup table for admin-configurable user roles"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(50), unique=True, nullable=False, index=True
    )  # super_admin, billing_manager, etc.
    name = Column(String(100), nullable=False)  # Display name
    description = Column(String(255))  # Detailed description
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System roles cannot be deleted
    sort_order = Column(Integer, default=0)  # For ordering in UI

    # Role properties
    is_admin_role = Column(Boolean, default=False)  # Is this an administrative role
    max_users = Column(Integer)  # Maximum users that can have this role (optional)
    requires_approval = Column(
        Boolean, default=False
    )  # Does assignment require approval

    # UI properties
    color_hex = Column(String(7), default="#6B7280")  # Color for role badges (#RRGGBB)
    icon_name = Column(String(50))  # Icon identifier for UI

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    role_permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    def __str__(self):
        return self.name
