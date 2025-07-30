from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.models.foundation.base import Base


class ServiceType(Base):
    """Service type lookup table for admin-configurable service categories"""
    __tablename__ = "service_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # internet, voip, tv, etc.
    name = Column(String(100), nullable=False)  # Display name
    description = Column(Text)  # Detailed description
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # System types cannot be deleted
    sort_order = Column(Integer, default=0)  # For ordering in UI
    
    # Service properties
    requires_installation = Column(Boolean, default=True)  # Does this service need installation
    supports_bandwidth_limits = Column(Boolean, default=True)  # Can bandwidth be limited
    is_recurring = Column(Boolean, default=True)  # Is this a recurring service
    allows_multiple_instances = Column(Boolean, default=False)  # Can customer have multiple of this type
    
    # Billing properties
    default_billing_cycle = Column(String(20), default="monthly")  # monthly, quarterly, yearly
    requires_equipment = Column(Boolean, default=False)  # Does service require equipment rental
    
    # UI properties
    color_hex = Column(String(7), default="#6B7280")  # Color for service type badges (#RRGGBB)
    icon_name = Column(String(50))  # Icon identifier for UI
    
    # Technical properties
    provisioning_template = Column(String(100))  # Template identifier for automation
    qos_profile = Column(String(50))  # Default QoS profile
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service_plans = relationship("ServicePlan", back_populates="service_type_ref")
    customer_services = relationship("CustomerService", back_populates="service_type_ref")
