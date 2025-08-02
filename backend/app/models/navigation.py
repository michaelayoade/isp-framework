"""
Navigation models for UI module and submodule registry.
"""
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class UIModule(Base):
    """UI Module registry for navigation."""
    __tablename__ = "ui_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    route = Column(String(200), nullable=False)
    order_idx = Column(Integer, nullable=False, default=0)
    is_enabled = Column(Boolean, nullable=False, default=True)
    tenant_scope = Column(String(20), nullable=False, default="GLOBAL")  # GLOBAL, RESELLER, CUSTOMER
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    submodules = relationship("UISubmodule", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UIModule(code='{self.code}', name='{self.name}')>"


class UISubmodule(Base):
    """UI Submodule registry for navigation."""
    __tablename__ = "ui_submodules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("ui_modules.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    route = Column(String(200), nullable=False)
    order_idx = Column(Integer, nullable=False, default=0)
    is_enabled = Column(Boolean, nullable=False, default=True)
    required_permission = Column(String(100), nullable=True)  # Permission code required to access
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    module = relationship("UIModule", back_populates="submodules")

    def __repr__(self):
        return f"<UISubmodule(code='{self.code}', name='{self.name}', module='{self.module.code if self.module else None}')>"

    class Config:
        from_attributes = True
