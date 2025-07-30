from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.models.foundation.base import Base


class CustomerStatus(Base):
    """Customer status lookup table for admin-configurable customer lifecycle statuses"""
    __tablename__ = "customer_statuses"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # new, active, suspended, etc.
    name = Column(String(100), nullable=False)  # Display name
    description = Column(String(255))  # Optional description
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System statuses cannot be deleted
    sort_order = Column(Integer, default=0)  # For ordering in UI
    
    # Workflow properties
    allows_service_activation = Column(Boolean, default=True)  # Can services be activated in this status
    allows_billing = Column(Boolean, default=True)  # Should billing continue in this status
    is_terminal = Column(Boolean, default=False)  # Is this a final status (terminated, cancelled)
    
    # UI properties
    color_hex = Column(String(7), default="#6B7280")  # Color for status badges (#RRGGBB)
    icon_name = Column(String(50))  # Icon identifier for UI
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customers = relationship("Customer", back_populates="status_ref")
