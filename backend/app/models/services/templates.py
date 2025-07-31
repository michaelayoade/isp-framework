"""
ISP Service Management System - Service Templates

Service templates define the available services that can be sold to customers.
These are the "products" in the catalog that customers can subscribe to.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, Text, ForeignKey, ARRAY, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.services.enums import (
    ServiceType, ServiceCategory, ServiceSubcategory, QualityProfile,
    SupportLevel, TrafficPriority, ContentFilterLevel
)


class ServiceTemplate(Base):
    """Base template for all service types - what's available to sell"""
    __tablename__ = "service_templates"

    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(Enum(ServiceType), nullable=False, index=True)
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    short_description = Column(String(500))
    
    # Pricing Integration (links to enhanced tariff system)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=False)
    
    # Service Categories
    category = Column(Enum(ServiceCategory), default=ServiceCategory.RESIDENTIAL)
    subcategory = Column(Enum(ServiceSubcategory))
    
    # Availability
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True)    # Visible on website
    is_featured = Column(Boolean, default=False) # Featured on homepage
    
    # Ordering
    display_order = Column(Integer, default=0)
    minimum_contract_months = Column(Integer)
    
    # Prerequisites
    requires_site_survey = Column(Boolean, default=False)
    requires_credit_check = Column(Boolean, default=False)
    minimum_credit_score = Column(Integer)
    
    # Geographic Availability
    available_locations = Column(JSONB, default=list)  # Location IDs where available
    
    # Technical Requirements
    equipment_required = Column(JSONB, default=list)   # Required equipment list
    technical_specs = Column(JSONB, default=dict)      # Technical specifications
    
    # Marketing
    marketing_tags = Column(ARRAY(String), default=list)
    promotional_text = Column(Text)
    terms_and_conditions = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tariff = relationship("Tariff", back_populates="service_templates")
    internet_config = relationship("InternetServiceTemplate", back_populates="service_template", uselist=False)
    voice_config = relationship("VoiceServiceTemplate", back_populates="service_template", uselist=False)
    bundle_config = relationship("BundleServiceTemplate", back_populates="service_template", uselist=False)
    customer_services = relationship("CustomerService", back_populates="service_template")

    def __repr__(self):
        return f"<ServiceTemplate {self.name}: {self.service_type.value}>"

    @property
    def is_available(self):
        """Check if service template is available for new subscriptions"""
        return self.is_active and self.is_public

    @property
    def base_price(self):
        """Get base price from linked tariff"""
        return self.tariff.base_price if self.tariff else None

    @property
    def setup_fee(self):
        """Get setup fee from linked tariff"""
        return self.tariff.setup_fee if self.tariff else None


class InternetServiceTemplate(Base):
    """Internet service template configuration"""
    __tablename__ = "internet_service_templates"

    service_template_id = Column(Integer, ForeignKey("service_templates.id", ondelete="CASCADE"), primary_key=True)
    
    # Speed Configuration
    download_speed_kbps = Column(Integer, nullable=False)
    upload_speed_kbps = Column(Integer, nullable=False)
    guaranteed_speed_percent = Column(Integer, default=10)  # Minimum guaranteed speed
    
    # Data Limits & FUP
    monthly_data_limit_gb = Column(Integer)  # null = unlimited
    fup_enabled = Column(Boolean, default=False)
    fup_threshold_gb = Column(Integer)
    fup_speed_down_kbps = Column(Integer)
    fup_speed_up_kbps = Column(Integer)
    
    # Network Configuration
    default_router_profile = Column(String(100))     # MikroTik profile name
    ip_pool_type = Column(String(20), default='dynamic')  # dynamic, static
    static_ip_required = Column(Boolean, default=False)
    
    # Quality Settings
    traffic_priority = Column(Enum(TrafficPriority), default=TrafficPriority.NORMAL)
    burst_enabled = Column(Boolean, default=False)
    burst_threshold_percent = Column(Integer, default=75)
    burst_time_seconds = Column(Integer, default=8)
    burst_limit_kbps = Column(Integer)
    
    # Protocol & Port Management
    blocked_ports = Column(ARRAY(Integer), default=list)      # [25, 135, 445]
    allowed_protocols = Column(ARRAY(String), default=list)   # [] = all allowed
    content_filtering_level = Column(Enum(ContentFilterLevel), default=ContentFilterLevel.NONE)
    custom_content_rules = Column(JSONB, default=dict)
    
    # Service Level
    uptime_sla_percent = Column(DECIMAL(5, 2), default=99.5)
    support_level = Column(Enum(SupportLevel), default=SupportLevel.STANDARD)
    
    # Advanced Features
    ipv6_enabled = Column(Boolean, default=True)
    port_forwarding_allowed = Column(Boolean, default=True)
    vpn_allowed = Column(Boolean, default=True)
    p2p_allowed = Column(Boolean, default=True)
    
    # Monitoring
    bandwidth_monitoring = Column(Boolean, default=True)
    usage_alerts_enabled = Column(Boolean, default=True)
    speed_test_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service_template = relationship("ServiceTemplate", back_populates="internet_config")

    @property
    def speed_display(self):
        """Human-readable speed"""
        def format_speed(kbps):
            if kbps >= 1000000:
                return f"{kbps/1000000:.1f}Gbps"
            elif kbps >= 1000:
                return f"{kbps/1000:.0f}Mbps"
            else:
                return f"{kbps}Kbps"
        
        return f"{format_speed(self.download_speed_kbps)}/{format_speed(self.upload_speed_kbps)}"

    @property
    def data_limit_display(self):
        """Human-readable data limit"""
        if not self.monthly_data_limit_gb:
            return "Unlimited"
        
        if self.monthly_data_limit_gb >= 1000:
            return f"{self.monthly_data_limit_gb/1000:.1f}TB"
        else:
            return f"{self.monthly_data_limit_gb}GB"

    @property
    def guaranteed_speed_kbps(self):
        """Calculate guaranteed minimum speed"""
        return {
            'download': int(self.download_speed_kbps * self.guaranteed_speed_percent / 100),
            'upload': int(self.upload_speed_kbps * self.guaranteed_speed_percent / 100)
        }


class VoiceServiceTemplate(Base):
    """Voice service template configuration"""
    __tablename__ = "voice_service_templates"

    service_template_id = Column(Integer, ForeignKey("service_templates.id", ondelete="CASCADE"), primary_key=True)
    
    # Voice Configuration
    included_minutes = Column(Integer, default=0)
    per_minute_rate = Column(DECIMAL(6, 4), nullable=False)
    
    # Call Features
    caller_id = Column(Boolean, default=True)
    call_waiting = Column(Boolean, default=True)
    call_forwarding = Column(Boolean, default=True)
    voicemail = Column(Boolean, default=True)
    three_way_calling = Column(Boolean, default=False)
    call_recording = Column(Boolean, default=False)
    
    # Advanced Features
    auto_attendant = Column(Boolean, default=False)
    conference_calling = Column(Boolean, default=False)
    call_transfer = Column(Boolean, default=True)
    do_not_disturb = Column(Boolean, default=True)
    
    # Technical Configuration
    codec_priority = Column(ARRAY(String), default=['G.711', 'G.729'])
    quality_profile = Column(Enum(QualityProfile), default=QualityProfile.STANDARD)
    
    # Routing
    number_range_start = Column(String(20))
    number_range_end = Column(String(20))
    area_code = Column(String(10))
    country_code = Column(String(5), default='+234')  # Nigeria
    
    # Call Restrictions
    international_calling = Column(Boolean, default=False)
    premium_numbers_allowed = Column(Boolean, default=False)
    blocked_number_patterns = Column(ARRAY(String), default=list)
    
    # Billing
    billing_increment_seconds = Column(Integer, default=60)  # Bill per minute
    minimum_call_charge_seconds = Column(Integer, default=60)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service_template = relationship("ServiceTemplate", back_populates="voice_config")

    @property
    def features_summary(self):
        """Get summary of enabled features"""
        features = []
        if self.caller_id:
            features.append("Caller ID")
        if self.call_waiting:
            features.append("Call Waiting")
        if self.call_forwarding:
            features.append("Call Forwarding")
        if self.voicemail:
            features.append("Voicemail")
        if self.three_way_calling:
            features.append("3-Way Calling")
        if self.call_recording:
            features.append("Call Recording")
        if self.auto_attendant:
            features.append("Auto Attendant")
        if self.conference_calling:
            features.append("Conference Calling")
        
        return features

    @property
    def minutes_display(self):
        """Human-readable minutes display"""
        if self.included_minutes == 0:
            return "Pay-per-minute"
        elif self.included_minutes >= 1000:
            return f"{self.included_minutes // 1000}k minutes included"
        else:
            return f"{self.included_minutes} minutes included"


class BundleServiceTemplate(Base):
    """Bundle service template for combined services"""
    __tablename__ = "bundle_service_templates"

    service_template_id = Column(Integer, ForeignKey("service_templates.id", ondelete="CASCADE"), primary_key=True)
    
    # Bundle Configuration
    included_services = Column(JSONB, nullable=False)  # List of service template IDs
    bundle_discount_percent = Column(DECIMAL(5, 2), default=0)
    bundle_discount_amount = Column(DECIMAL(10, 2), default=0)
    
    # Bundle Rules
    minimum_services = Column(Integer, default=2)
    maximum_services = Column(Integer)
    allow_service_customization = Column(Boolean, default=False)
    
    # Contract Terms
    minimum_bundle_months = Column(Integer, default=12)
    early_termination_fee = Column(DECIMAL(10, 2))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    service_template = relationship("ServiceTemplate", back_populates="bundle_config")

    @property
    def total_individual_price(self):
        """Calculate total price if services bought individually"""
        # This would need to be calculated based on included services
        # Implementation would query the individual service templates
        pass

    @property
    def bundle_savings(self):
        """Calculate savings from bundle pricing"""
        # Implementation would compare bundle price vs individual prices
        pass


# Performance indexes
from sqlalchemy import Index

# Service template indexes
Index('idx_service_templates_type_active', ServiceTemplate.service_type, ServiceTemplate.is_active)
Index('idx_service_templates_category', ServiceTemplate.category, ServiceTemplate.is_active)
Index('idx_service_templates_featured', ServiceTemplate.is_featured, ServiceTemplate.display_order)
Index('idx_service_templates_public', ServiceTemplate.is_public, ServiceTemplate.is_active)

# Internet service template indexes
Index('idx_internet_templates_speed', InternetServiceTemplate.download_speed_kbps, InternetServiceTemplate.upload_speed_kbps)
Index('idx_internet_templates_fup', InternetServiceTemplate.fup_enabled)

# Voice service template indexes
Index('idx_voice_templates_minutes', VoiceServiceTemplate.included_minutes)
Index('idx_voice_templates_features', VoiceServiceTemplate.caller_id, VoiceServiceTemplate.voicemail)
