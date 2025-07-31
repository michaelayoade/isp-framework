from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.models.foundation.base import Base


class Permission(Base):
    """Permission lookup table for granular access control"""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(
        String(100), unique=True, nullable=False, index=True
    )  # customers.view, billing.create, etc.
    name = Column(String(150), nullable=False)  # Display name
    description = Column(String(255))  # Detailed description
    category = Column(
        String(50), nullable=False, index=True
    )  # customers, billing, tickets, etc.
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System permissions cannot be deleted
    sort_order = Column(Integer, default=0)  # For ordering in UI

    # Permission properties
    resource = Column(String(50), nullable=False)  # customers, invoices, tickets, etc.
    action = Column(
        String(50), nullable=False
    )  # view, create, update, delete, export, etc.
    scope = Column(String(50), default="all")  # all, own, assigned, department, etc.

    # UI properties
    icon_name = Column(String(50))  # Icon identifier for UI

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")

    def __str__(self):
        return f"{self.resource}.{self.action}"
