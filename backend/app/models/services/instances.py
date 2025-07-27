"""
ISP Service Management System - Customer Service Instances

Customer service instances represent actual services assigned to customers.
These are the "subscriptions" - services that customers are actively using.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, Text, ForeignKey, ARRAY, Enum
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.services.enums import (
    ServiceStatus, ConnectionType, IPAssignmentType, BillingModel
)
from datetime import datetime, timedelta


class CustomerService(Base):
    """Actual service instances assigned to customers"""
    __tablename__ = "customer_services"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    service_template_id = Column(Integer, ForeignKey("service_templates.id"), nullable=False)
    
    # Service Identity
    service_number = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(255))  # Customer-friendly name
    
    # Service Status
    status = Column(Enum(ServiceStatus), default=ServiceStatus.PENDING, index=True)
    substatus = Column(String(100))  # Additional status details
    
    # Service Period
    activation_date = Column(DateTime(timezone=True), index=True)
    termination_date = Column(DateTime(timezone=True))
    contract_start_date = Column(DateTime(timezone=True))
    contract_end_date = Column(DateTime(timezone=True))
    
    # Billing Integration
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=False)
    billing_option_id = Column(Integer, ForeignKey("tariff_billing_options.id"))
    billing_model = Column(Enum(BillingModel), default=BillingModel.POSTPAID)
    
    # Service Location
    service_address = Column(Text)
    installation_address = Column(Text)  # May differ from service address
    latitude = Column(String(20))
    longitude = Column(String(20))
    
    # Pricing Overrides (if different from tariff)
    custom_price = Column(DECIMAL(12, 2))
    discount_percentage = Column(DECIMAL(5, 2), default=0)
    promotional_pricing = Column(Boolean, default=False)
    promotional_end_date = Column(DateTime(timezone=True))
    
    # Network Assignment
    primary_router_id = Column(Integer, ForeignKey("routers.id"))
    backup_router_id = Column(Integer, ForeignKey("routers.id"))
    sector_id = Column(Integer, ForeignKey("router_sectors.id"))
    
    # Service Configuration (can override template defaults)
    service_config = Column(JSONB, default=dict)  # Service-specific overrides
    
    # Customer Preferences
    maintenance_window = Column(String(100))  # Preferred maintenance hours
    contact_preferences = Column(JSONB, default=dict)
    
    # Service History
    previous_service_id = Column(Integer, ForeignKey("customer_services.id"))  # For upgrades/downgrades
    change_reason = Column(String(255))
    
    # Quality Metrics
    average_uptime_percent = Column(DECIMAL(5, 2))
    last_outage_date = Column(DateTime(timezone=True))
    total_outage_minutes = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="services")
    service_template = relationship("ServiceTemplate", back_populates="customer_services")
    tariff = relationship("Tariff", back_populates="customer_services")
    billing_option = relationship("TariffBillingOption")
    primary_router = relationship("Router", foreign_keys=[primary_router_id])
    backup_router = relationship("Router", foreign_keys=[backup_router_id])
    
    # Service-specific configurations
    internet_config = relationship("CustomerInternetService", back_populates="customer_service", uselist=False)
    voice_config = relationship("CustomerVoiceService", back_populates="customer_service", uselist=False)
    
    # Service management
    provisioning = relationship("ServiceProvisioning", back_populates="customer_service", uselist=False)
    ip_assignments = relationship("ServiceIPAssignment", back_populates="customer_service")
    status_history = relationship("ServiceStatusHistory", back_populates="customer_service")
    suspensions = relationship("ServiceSuspension", back_populates="customer_service")

    def __repr__(self):
        return f"<CustomerService {self.service_number}: {self.customer_id} - {self.status.value}>"

    @property
    def is_active(self):
        """Check if service is currently active"""
        return self.status == ServiceStatus.ACTIVE

    @property
    def contract_months_remaining(self):
        """Calculate remaining contract months"""
        if not self.contract_end_date:
            return 0
        
        now = datetime.now(self.contract_end_date.tzinfo)
        if now >= self.contract_end_date:
            return 0
        
        delta = self.contract_end_date - now
        return max(0, round(delta.days / 30.44))  # Average days per month

    @property
    def effective_price(self):
        """Calculate effective service price including discounts"""
        base_price = self.custom_price or (self.tariff.base_price if self.tariff else 0)
        if self.discount_percentage > 0:
            return base_price * (1 - self.discount_percentage / 100)
        return base_price

    @property
    def service_age_days(self):
        """Calculate service age in days"""
        if not self.activation_date:
            return 0
        
        now = datetime.now(self.activation_date.tzinfo)
        return (now - self.activation_date).days

    @property
    def is_under_contract(self):
        """Check if service is still under contract"""
        if not self.contract_end_date:
            return False
        
        now = datetime.now(self.contract_end_date.tzinfo)
        return now < self.contract_end_date


class CustomerInternetService(Base):
    """Internet-specific service configuration for customers"""
    __tablename__ = "customer_internet_service_instances"

    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), primary_key=True)
    
    # PPPoE Configuration
    pppoe_username = Column(String(255), unique=True, index=True)
    pppoe_password = Column(String(255))
    
    # Speed Configuration (may override template)
    download_speed_kbps = Column(Integer)
    upload_speed_kbps = Column(Integer)
    
    # Current Speed Limits (for FUP or temporary changes)
    current_speed_down_kbps = Column(Integer)
    current_speed_up_kbps = Column(Integer)
    speed_limited = Column(Boolean, default=False)
    speed_limit_reason = Column(String(100))
    speed_limit_until = Column(DateTime(timezone=True))
    
    # FUP Status
    fup_exceeded = Column(Boolean, default=False)
    fup_reset_date = Column(DateTime(timezone=True))
    monthly_usage_gb = Column(DECIMAL(10, 2), default=0)
    daily_usage_gb = Column(DECIMAL(8, 2), default=0)
    
    # Router Configuration
    router_profile = Column(String(100))    # Applied MikroTik profile
    queue_name = Column(String(255))        # MikroTik queue name
    
    # Connection Details
    nas_port = Column(String(50))           # Physical port on router
    vlan_id = Column(Integer)               # VLAN assignment
    connection_type = Column(Enum(ConnectionType), default=ConnectionType.PPPOE)
    
    # Quality Monitoring
    last_speed_test_down = Column(Integer)  # Last measured download speed
    last_speed_test_up = Column(Integer)    # Last measured upload speed
    last_speed_test_date = Column(DateTime(timezone=True))
    last_ping_ms = Column(DECIMAL(6, 2))    # Last ping latency
    
    # Usage Statistics
    total_download_gb = Column(DECIMAL(12, 2), default=0)
    total_upload_gb = Column(DECIMAL(12, 2), default=0)
    peak_usage_date = Column(DateTime(timezone=True))
    peak_usage_gb = Column(DECIMAL(8, 2))
    
    # MAC Address Binding (if required)
    bound_mac_addresses = Column(ARRAY(String), default=list)
    mac_binding_enabled = Column(Boolean, default=False)
    
    # Session Information
    last_session_start = Column(DateTime(timezone=True))
    last_session_end = Column(DateTime(timezone=True))
    total_session_time_hours = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_service = relationship("CustomerService", back_populates="internet_config")

    # Traffic counters relationships
    traffic_counters = relationship(
        "CustomerTrafficCounter",
        back_populates="internet_service",
        uselist=False,
        cascade="all, delete-orphan",
        overlaps="internet_service,customer_service"
    )
    bonus_traffic_counters = relationship(
        "CustomerBonusTrafficCounter",
        back_populates="internet_service",
        uselist=False,
        cascade="all, delete-orphan",
        overlaps="internet_service,customer_service"
    )

    @property
    def effective_speed_display(self):
        """Get current effective speed (considering limitations)"""
        down_speed = self.current_speed_down_kbps or self.download_speed_kbps
        up_speed = self.current_speed_up_kbps or self.upload_speed_kbps
        
        def format_speed(kbps):
            if kbps >= 1000000:
                return f"{kbps/1000000:.1f}Gbps"
            elif kbps >= 1000:
                return f"{kbps/1000:.0f}Mbps"
            else:
                return f"{kbps}Kbps"
        
        return f"{format_speed(down_speed)}/{format_speed(up_speed)}"

    @property
    def monthly_usage_percent(self):
        """Calculate monthly usage percentage (if limit exists)"""
        if not hasattr(self.customer_service.service_template, 'internet_config'):
            return 0
        
        template = self.customer_service.service_template.internet_config
        if not template or not template.monthly_data_limit_gb:
            return 0
        
        return min(100, (float(self.monthly_usage_gb) / template.monthly_data_limit_gb) * 100)

    @property
    def is_online(self):
        """Check if customer is currently online"""
        if not self.last_session_start:
            return False
        
        if self.last_session_end and self.last_session_end > self.last_session_start:
            return False
        
        # Consider online if session started within last 10 minutes without end
        now = datetime.now(self.last_session_start.tzinfo)
        return (now - self.last_session_start).total_seconds() < 600


class CustomerVoiceService(Base):
    """Voice-specific service configuration for customers"""
    __tablename__ = "customer_voice_service_instances"

    customer_service_id = Column(Integer, ForeignKey("customer_services.id", ondelete="CASCADE"), primary_key=True)
    
    # Phone Number Assignment
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    secondary_numbers = Column(ARRAY(String), default=list)
    
    # Voice Configuration
    voicemail_enabled = Column(Boolean, default=True)
    voicemail_pin = Column(String(10))
    call_forwarding_number = Column(String(20))
    call_forwarding_enabled = Column(Boolean, default=False)
    
    # Usage Tracking
    monthly_minutes_used = Column(Integer, default=0)
    minutes_reset_date = Column(DateTime(timezone=True))
    total_minutes_lifetime = Column(Integer, default=0)
    
    # Call Statistics
    total_incoming_calls = Column(Integer, default=0)
    total_outgoing_calls = Column(Integer, default=0)
    total_missed_calls = Column(Integer, default=0)
    average_call_duration_seconds = Column(Integer, default=0)
    
    # Technical Configuration
    sip_username = Column(String(255), unique=True)
    sip_password = Column(String(255))
    sip_domain = Column(String(255))
    sip_port = Column(Integer, default=5060)
    
    # Call Features Status
    caller_id_enabled = Column(Boolean, default=True)
    call_waiting_enabled = Column(Boolean, default=True)
    three_way_calling_enabled = Column(Boolean, default=False)
    do_not_disturb_enabled = Column(Boolean, default=False)
    
    # Call Restrictions
    international_calling_enabled = Column(Boolean, default=False)
    premium_numbers_blocked = Column(Boolean, default=True)
    blocked_numbers = Column(ARRAY(String), default=list)
    
    # Voicemail Settings
    voicemail_greeting_custom = Column(Boolean, default=False)
    voicemail_email_notification = Column(Boolean, default=False)
    voicemail_max_messages = Column(Integer, default=20)
    
    # Last Activity
    last_incoming_call = Column(DateTime(timezone=True))
    last_outgoing_call = Column(DateTime(timezone=True))
    last_registration = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer_service = relationship("CustomerService", back_populates="voice_config")

    @property
    def minutes_remaining(self):
        """Calculate remaining included minutes"""
        if not hasattr(self.customer_service.service_template, 'voice_config'):
            return 0
        
        template = self.customer_service.service_template.voice_config
        if not template or template.included_minutes == 0:
            return 0  # Pay-per-minute service
        
        return max(0, template.included_minutes - self.monthly_minutes_used)

    @property
    def minutes_usage_percent(self):
        """Calculate percentage of included minutes used"""
        if not hasattr(self.customer_service.service_template, 'voice_config'):
            return 0
        
        template = self.customer_service.service_template.voice_config
        if not template or template.included_minutes == 0:
            return 0
        
        return min(100, (self.monthly_minutes_used / template.included_minutes) * 100)

    @property
    def is_registered(self):
        """Check if phone is currently registered"""
        if not self.last_registration:
            return False
        
        # Consider registered if last registration was within 5 minutes
        now = datetime.now(self.last_registration.tzinfo)
        return (now - self.last_registration).total_seconds() < 300

    @property
    def formatted_phone_number(self):
        """Format phone number for display"""
        if not self.phone_number:
            return ""
        
        # Nigerian phone number formatting
        number = self.phone_number.replace('+234', '').replace(' ', '').replace('-', '')
        if len(number) == 10:
            return f"+234 {number[:3]} {number[3:6]} {number[6:]}"
        elif len(number) == 11 and number.startswith('0'):
            return f"+234 {number[1:4]} {number[4:7]} {number[7:]}"
        else:
            return self.phone_number


# Performance indexes
from sqlalchemy import Index

# Customer service indexes
Index('idx_customer_services_customer_status', CustomerService.customer_id, CustomerService.status)
Index('idx_customer_services_template', CustomerService.service_template_id)
Index('idx_customer_services_router', CustomerService.primary_router_id)
Index('idx_customer_services_activation', CustomerService.activation_date)
Index('idx_customer_services_contract', CustomerService.contract_end_date)

# Internet service indexes
Index('idx_internet_services_username', CustomerInternetService.pppoe_username)
Index('idx_internet_services_fup', CustomerInternetService.fup_exceeded)
Index('idx_internet_services_speed_limited', CustomerInternetService.speed_limited)
Index('idx_internet_services_session', CustomerInternetService.last_session_start)

# Voice service indexes
Index('idx_voice_services_phone', CustomerVoiceService.phone_number)
Index('idx_voice_services_sip', CustomerVoiceService.sip_username)
Index('idx_voice_services_registration', CustomerVoiceService.last_registration)
