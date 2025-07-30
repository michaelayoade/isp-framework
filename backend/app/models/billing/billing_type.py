from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.models.foundation.base import Base


class BillingType(Base):
    """Billing type lookup table for admin-configurable payment models"""
    __tablename__ = "billing_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # recurring, prepaid_daily, etc.
    name = Column(String(100), nullable=False)  # Display name
    description = Column(String(255))  # Optional description
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System types cannot be deleted
    sort_order = Column(Integer, default=0)  # For ordering in UI
    
    # Billing properties
    is_recurring = Column(Boolean, default=True)  # Is this a recurring billing model
    requires_prepayment = Column(Boolean, default=False)  # Must customer prepay
    supports_prorating = Column(Boolean, default=True)  # Can be prorated for partial periods
    default_cycle_days = Column(Integer, default=30)  # Default billing cycle in days
    
    # Payment properties
    allows_partial_payments = Column(Boolean, default=False)  # Can customer pay partially
    auto_suspend_on_overdue = Column(Boolean, default=True)  # Auto-suspend when overdue
    grace_period_days = Column(Integer, default=3)  # Grace period before suspension
    
    # Credit properties
    supports_credit_limit = Column(Boolean, default=False)  # Does this type support credit limits
    default_credit_limit = Column(Integer, default=0)  # Default credit limit (in cents)
    
    # UI properties
    color_hex = Column(String(7), default="#6B7280")  # Color for billing type badges (#RRGGBB)
    icon_name = Column(String(50))  # Icon identifier for UI
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customers = relationship("Customer", back_populates="billing_type_ref")
    service_plans = relationship("ServicePlan", back_populates="billing_type_ref")
