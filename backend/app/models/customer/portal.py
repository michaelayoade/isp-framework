"""
Portal Configuration Models

Models for managing portal ID configuration and history.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class PortalConfig(Base):
    """Portal ID configuration for different partners and service types"""

    __tablename__ = "portal_config"

    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(Integer, ForeignKey("resellers.id"), nullable=True)
    prefix = Column(String(20), nullable=False, index=True)
    description = Column(Text)
    service_type = Column(String(50), nullable=False, default="internet", index=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reseller = relationship("Reseller", back_populates="portal_configs")

    def __repr__(self):
        return f"<PortalConfig(id={self.id}, reseller_id={self.reseller_id}, prefix='{self.prefix}', service_type='{self.service_type}')>"


class PortalIDHistory(Base):
    """Portal ID change history for auditing"""

    __tablename__ = "portal_id_history"

    id = Column(Integer, primary_key=True, index=True)
    reseller_id = Column(
        Integer, ForeignKey("resellers.id"), nullable=True
    )  # Updated to reference resellers table
    old_portal_id = Column(String(50))
    new_portal_id = Column(String(50), nullable=False)
    changed_by = Column(Integer, ForeignKey("administrators.id", ondelete="SET NULL"))
    change_reason = Column(Text)
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    # customer = relationship("CustomerExtended")  # Disabled due to missing FK
    admin = relationship("Administrator")

    def __repr__(self):
        return f"<PortalIDHistory(id={self.id}, customer_id={self.customer_id}, old='{self.old_portal_id}', new='{self.new_portal_id}')>"
