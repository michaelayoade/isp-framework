"""
Service Management Models

This module contains SQLAlchemy models for different service types:
Internet services, Voice services, Bundle services, and Recurring services.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class InternetService(Base):
    """Internet service configurations and tariff plans"""
    __tablename__ = "internet_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Service configuration
    download_speed = Column(Integer, nullable=False)  # Mbps
    upload_speed = Column(Integer, nullable=False)    # Mbps
    data_limit = Column(Integer)  # GB, null = unlimited
    
    # Tariff reference (pricing handled by tariff module)
    tariff_id = Column(Integer, ForeignKey("internet_tariffs.id"))
    
    # Network configuration
    router_id = Column(Integer, ForeignKey("routers.id"))
    sector_id = Column(Integer, ForeignKey("router_sectors.id"))
    ip_pool_id = Column(Integer, ForeignKey("ip_pools.id"))
    
    # Service settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Visible to customers
    priority = Column(Integer, default=0)  # Higher = more priority
    
    # RADIUS integration
    radius_profile = Column(String(100))  # MikroTik profile name
    bandwidth_limit_down = Column(String(50))  # e.g., "100M/100M"
    bandwidth_limit_up = Column(String(50))
    
    # Service lifecycle
    activation_method = Column(String(50), default="manual")  # manual, auto
    provisioning_script = Column(Text)  # Custom provisioning commands
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    router = relationship("Router", foreign_keys=[router_id])
    sector = relationship("RouterSector", foreign_keys=[sector_id])
    ip_pool = relationship("IPPool", foreign_keys=[ip_pool_id])
    
    def __repr__(self):
        return f"<InternetService(id={self.id}, name='{self.name}', speed={self.download_speed}/{self.upload_speed})>"
    
    @property
    def speed_display(self):
        """Human-readable speed display"""
        return f"{self.download_speed}/{self.upload_speed} Mbps"
    
    @property
    def data_limit_display(self):
        """Human-readable data limit display"""
        if self.data_limit:
            return f"{self.data_limit} GB"
        return "Unlimited"


class VoiceService(Base):
    """Voice service configurations and tariff plans"""
    __tablename__ = "voice_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Service configuration
    included_minutes = Column(Integer, default=0)  # Monthly included minutes
    per_minute_rate = Column(DECIMAL(6, 4), nullable=False)  # Rate per minute
    
    # Tariff reference (pricing handled by tariff module)
    tariff_id = Column(Integer, ForeignKey("voice_tariffs.id"))
    
    # Voice configuration
    codec = Column(String(50), default="G.711")
    quality = Column(String(50), default="standard")  # standard, premium
    
    # Service settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Call routing
    route_prefix = Column(String(20))  # Routing prefix
    gateway_id = Column(Integer)  # Voice gateway reference
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<VoiceService(id={self.id}, name='{self.name}', rate={self.per_minute_rate})>"
    
    @property
    def minutes_display(self):
        """Human-readable minutes display"""
        if self.included_minutes > 0:
            return f"{self.included_minutes} minutes included"
        return "Pay per minute"


class BundleService(Base):
    """Bundle service packages combining multiple services"""
    __tablename__ = "bundle_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Bundle configuration
    internet_service_id = Column(Integer, ForeignKey("internet_services.id"))
    voice_service_id = Column(Integer, ForeignKey("voice_services.id"))
    
    # Tariff reference (pricing handled by tariff module)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"))
    
    # Bundle settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Contract terms
    minimum_term_months = Column(Integer, default=12)
    early_termination_fee = Column(DECIMAL(10, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    internet_service = relationship("InternetService", foreign_keys=[internet_service_id])
    voice_service = relationship("VoiceService", foreign_keys=[voice_service_id])
    
    def __repr__(self):
        return f"<BundleService(id={self.id}, name='{self.name}', price={self.bundle_price})>"
    
    @property
    def savings_amount(self):
        """Calculate savings from bundle pricing"""
        if self.individual_price:
            return self.individual_price - self.bundle_price
        return 0
    
    @property
    def savings_percentage(self):
        """Calculate savings percentage"""
        if self.individual_price and self.individual_price > 0:
            return ((self.individual_price - self.bundle_price) / self.individual_price) * 100
        return 0


class RecurringService(Base):
    """Recurring services and add-ons"""
    __tablename__ = "recurring_services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Service configuration
    service_type = Column(String(50), nullable=False)  # addon, maintenance, support
    billing_cycle = Column(String(20), default="monthly")  # monthly, quarterly, yearly
    
    # Tariff reference (pricing handled by tariff module)
    tariff_id = Column(Integer, ForeignKey("recurring_tariffs.id"))
    
    # Service settings
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    is_addon = Column(Boolean, default=True)  # Can be added to other services
    
    # Automation
    auto_provision = Column(Boolean, default=False)
    provisioning_script = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RecurringService(id={self.id}, name='{self.name}', type='{self.service_type}')>"


class ServicePlan(Base):
    """Legacy service plan model for backward compatibility"""
    __tablename__ = "service_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    service_type = Column(String(50), default="internet")  # internet, voice, bundle
    price = Column(Integer, nullable=False)  # Price in cents
    currency = Column(String(3), default="NGN")
    billing_cycle = Column(String(20), default="monthly")  # monthly, quarterly, yearly
    
    # Internet service specific fields
    download_speed = Column(Integer)  # Mbps
    upload_speed = Column(Integer)    # Mbps
    data_limit = Column(Integer)      # GB, null for unlimited
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer_services = relationship("CustomerService", back_populates="service_plan")


class CustomerService(Base):
    """Legacy customer service assignment model for backward compatibility"""
    __tablename__ = "customer_services"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_plan_id = Column(Integer, ForeignKey("service_plans.id"), nullable=False)
    status = Column(String(20), default="active")  # active, suspended, terminated
    
    # Service period
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    
    # Pricing overrides
    custom_price = Column(Integer)  # Override service plan price
    discount_percentage = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="services")
    service_plan = relationship("ServicePlan", back_populates="customer_services")



