"""
RADIUS Session Management Models
Comprehensive RADIUS session tracking with ISP-specific features,
FUP integration, multi-session support, and proper RADIUS attribute handling
"""

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, DECIMAL, ForeignKey, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime, timedelta


class SessionStatus(enum.Enum):
    STARTING = "starting"     # Accounting-Start received
    ACTIVE = "active"         # Session established
    INTERIM = "interim"       # Interim update received  
    STOPPING = "stopping"     # Disconnect initiated
    STOPPED = "stopped"       # Accounting-Stop received
    FAILED = "failed"         # Session failed to start


class DisconnectCause(enum.Enum):
    USER_REQUEST = "user_request"
    ADMIN_DISCONNECT = "admin_disconnect"
    IDLE_TIMEOUT = "idle_timeout"
    SESSION_TIMEOUT = "session_timeout"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    FUP_EXCEEDED = "fup_exceeded"
    NETWORK_ERROR = "network_error"
    NAS_REBOOT = "nas_reboot"
    UNKNOWN = "unknown"


class SessionType(enum.Enum):
    PPPOE = "pppoe"
    HOTSPOT = "hotspot"
    DOT1X = "dot1x"
    DHCP = "dhcp"
    STATIC = "static"


class RadiusSession(Base):
    """Comprehensive RADIUS session tracking"""
    __tablename__ = "radius_sessions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Core Identifiers
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"))
    service_id = Column(Integer, ForeignKey("customer_services.id"))
    
    # Authentication Details
    username = Column(String(255), nullable=False, index=True)
    realm = Column(String(255))  # domain.com part of user@domain.com
    session_type = Column(Enum(SessionType), default=SessionType.PPPOE)
    
    # RADIUS Attributes (Standard)
    calling_station_id = Column(String(50))      # Client MAC/Phone number
    called_station_id = Column(String(50))       # NAS MAC/SSID
    nas_port_id = Column(String(50))             # Physical port identifier
    nas_port_type = Column(String(50))           # Ethernet, Wireless, Virtual, etc.
    framed_protocol = Column(String(50))         # PPP, SLIP, ARAP, etc.
    service_type = Column(String(50))            # Framed-User, Login-User, etc.
    
    # Network Configuration
    framed_ip_address = Column(INET, index=True)
    framed_ipv6_address = Column(INET)
    framed_netmask = Column(INET)
    dns_server_1 = Column(INET)
    dns_server_2 = Column(INET)
    
    # Session Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    stop_time = Column(DateTime(timezone=True), index=True)
    session_timeout = Column(Integer)            # Maximum session duration (seconds)
    idle_timeout = Column(Integer)               # Idle timeout (seconds)
    
    # Traffic Accounting
    bytes_in = Column(BigInteger, default=0)
    bytes_out = Column(BigInteger, default=0)
    packets_in = Column(BigInteger, default=0)
    packets_out = Column(BigInteger, default=0)
    
    # Session State
    status = Column(Enum(SessionStatus), default=SessionStatus.STARTING, index=True)
    disconnect_cause = Column(Enum(DisconnectCause))
    disconnect_reason = Column(Text)
    
    # ISP-Specific Features
    tariff_id = Column(Integer, ForeignKey("tariffs.id"))
    
    # Traffic Shaping & FUP
    original_speed_down = Column(Integer)        # Original tariff speed (kbps)
    original_speed_up = Column(Integer)
    current_speed_down = Column(Integer)         # Current applied speed (may be limited)
    current_speed_up = Column(Integer)
    speed_limited = Column(Boolean, default=False)
    
    # Fair Usage Policy
    fup_exceeded = Column(Boolean, default=False)
    fup_exceeded_at = Column(DateTime(timezone=True))
    fup_reset_at = Column(DateTime(timezone=True))
    data_quota_bytes = Column(BigInteger)        # Assigned data quota
    data_used_bytes = Column(BigInteger, default=0)  # Used against quota
    
    # Billing
    session_cost = Column(DECIMAL(10, 4), default=0)
    billing_method = Column(String(50))          # postpaid, prepaid, free
    
    # Technical Details
    nas_ip_address = Column(INET)
    client_ip_address = Column(INET)             # Might differ from framed_ip
    tunnel_type = Column(String(50))             # L2TP, PPTP, GRE, etc.
    tunnel_medium_type = Column(String(50))      # IPv4, IPv6, etc.
    
    # Additional RADIUS Attributes (JSON for flexibility)
    radius_attributes = Column(JSONB, default={})
    
    # Performance Tracking
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    interim_interval = Column(Integer, default=300)  # Seconds between interim updates
    last_interim_update = Column(DateTime(timezone=True))
    
    # Legacy compatibility fields (for backward compatibility)
    login = Column(String(255), index=True)  # Maps to username
    username_real = Column(String(255))
    in_bytes = Column(BigInteger, default=0)  # Maps to bytes_in
    out_bytes = Column(BigInteger, default=0)  # Maps to bytes_out
    start_session = Column(DateTime(timezone=True), index=True)  # Maps to start_time
    end_session = Column(DateTime(timezone=True))  # Maps to stop_time
    ipv4 = Column(INET, index=True)  # Maps to framed_ip_address
    ipv6 = Column(INET)  # Maps to framed_ipv6_address
    mac = Column(String(17), index=True)  # Maps to calling_station_id
    call_to = Column(String(50))
    port = Column(String(50))  # Maps to nas_port_id
    price = Column(DECIMAL(10, 4), default=0)  # Maps to session_cost
    time_on = Column(Integer, default=0)
    last_change = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String(50), default="mikrotik_api")
    login_is = Column(String(20), default="user")
    partner_id = Column(Integer)
    nas_id = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    nas_device = relationship("NASDevice")
    customer = relationship("Customer")
    interim_updates = relationship("RADIUSInterimUpdate", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RadiusSession {self.session_id}: {self.username} ({self.status.value if self.status else 'unknown'})>"

    @property
    def total_bytes(self):
        """Total bytes transferred"""
        return (self.bytes_in or 0) + (self.bytes_out or 0)

    @property
    def total_gb(self):
        """Total data in GB"""
        return round(self.total_bytes / (1024**3), 2)

    @property
    def session_duration_seconds(self):
        """Current session duration in seconds"""
        if self.stop_time:
            return int((self.stop_time - self.start_time).total_seconds())
        elif self.start_time:
            return int((datetime.now(self.start_time.tzinfo) - self.start_time).total_seconds())
        return 0

    @property
    def session_duration_hours(self):
        """Session duration in hours"""
        return round(self.session_duration_seconds / 3600, 2)

    @property
    def is_active(self):
        """Check if session is currently active"""
        return self.status in [SessionStatus.ACTIVE, SessionStatus.INTERIM] and not self.stop_time

    @property
    def data_quota_remaining_gb(self):
        """Remaining data quota in GB"""
        if not self.data_quota_bytes:
            return None
        remaining_bytes = max(0, self.data_quota_bytes - (self.data_used_bytes or 0))
        return round(remaining_bytes / (1024**3), 2)

    @property
    def fup_percentage_used(self):
        """Percentage of FUP quota used"""
        if not self.data_quota_bytes:
            return 0
        return round((self.data_used_bytes or 0) / self.data_quota_bytes * 100, 1)

    def should_apply_fup(self):
        """Check if FUP should be applied"""
        if not self.data_quota_bytes or self.fup_exceeded:
            return False
        return (self.data_used_bytes or 0) >= self.data_quota_bytes

    def calculate_session_cost(self, tariff_config):
        """Calculate session cost based on tariff"""
        if not tariff_config:
            return 0
        
        # Implementation depends on billing method
        duration_hours = self.session_duration_hours
        data_gb = self.total_gb
        
        # Example: Time-based billing
        if self.billing_method == 'time_based':
            return duration_hours * getattr(tariff_config, 'hourly_rate', 0)
        
        # Example: Data-based billing  
        elif self.billing_method == 'data_based':
            return data_gb * getattr(tariff_config, 'per_gb_rate', 0)
        
        return 0


class RADIUSInterimUpdate(Base):
    """RADIUS interim accounting updates for long sessions"""
    __tablename__ = "radius_interim_updates"

    id = Column(Integer, primary_key=True, index=True)
    radius_session_id = Column(Integer, ForeignKey("radius_sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Update timing
    update_time = Column(DateTime(timezone=True), nullable=False, index=True)
    session_time = Column(Integer, nullable=False)  # Seconds since session start
    
    # Traffic at time of update
    bytes_in_total = Column(BigInteger, nullable=False)
    bytes_out_total = Column(BigInteger, nullable=False)
    packets_in_total = Column(BigInteger, default=0)
    packets_out_total = Column(BigInteger, default=0)
    
    # Delta since last update
    bytes_in_delta = Column(BigInteger, default=0)
    bytes_out_delta = Column(BigInteger, default=0)
    
    # FUP status at time of update
    fup_status = Column(Boolean, default=False)
    current_speed_down = Column(Integer)
    current_speed_up = Column(Integer)
    
    # Additional attributes
    radius_attributes = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("RadiusSession", foreign_keys=[radius_session_id], back_populates="interim_updates")


class CustomerOnline(Base):
    """Current online customers - optimized view table"""
    __tablename__ = "customers_online"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    
    # Current session info (denormalized for performance)
    current_session_id = Column(String(255), ForeignKey("radius_sessions.session_id"))
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"))
    
    # Quick access fields
    username = Column(String(255), index=True)
    login = Column(String(255), nullable=False, index=True)
    username_real = Column(String(255))
    
    # Network details
    ipv4 = Column(INET, index=True)
    ipv6 = Column(INET)
    mac = Column(String(17), index=True)
    framed_ip = Column(INET, index=True)
    session_start = Column(DateTime(timezone=True), index=True)
    start_session = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Current usage
    in_bytes = Column(BigInteger, default=0)
    out_bytes = Column(BigInteger, default=0)
    bytes_in = Column(BigInteger, default=0)
    bytes_out = Column(BigInteger, default=0)
    session_duration = Column(Integer, default=0)  # seconds
    time_on = Column(Integer, default=0)
    
    # Status indicators
    fup_exceeded = Column(Boolean, default=False)
    speed_limited = Column(Boolean, default=False)
    current_speed_down = Column(Integer)
    current_speed_up = Column(Integer)
    
    # Legacy fields for compatibility
    service_id = Column(Integer, ForeignKey("customer_services.id"))
    tariff_id = Column(Integer)
    partner_id = Column(Integer)
    nas_id = Column(Integer)
    call_to = Column(String(50))
    port = Column(String(50))
    price = Column(DECIMAL(10, 4), default=0)
    type = Column(String(50), default="mikrotik_api")
    login_is = Column(String(20), default="user")
    session_id = Column(String(255), unique=True, index=True)
    
    # Last update
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    last_change = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    customer = relationship("Customer")
    session = relationship("RadiusSession", foreign_keys=[current_session_id])

    def __repr__(self):
        return f"<CustomerOnline {self.login}: {self.ipv4}>"

    @property
    def total_bytes(self):
        """Total bytes transferred (in + out)"""
        return (self.in_bytes or 0) + (self.out_bytes or 0)

    @property
    def total_gb(self):
        """Total data usage in GB"""
        return round(self.total_bytes / (1024**3), 2)

    @property
    def session_hours(self):
        """Session duration in hours"""
        return round((self.session_duration or 0) / 3600, 2)

    @property
    def session_duration_minutes(self):
        """Session duration in minutes"""
        return round((self.time_on or 0) / 60, 2)


class CustomerStatistics(Base):
    """Aggregated customer usage statistics for reporting"""
    __tablename__ = "customer_statistics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Aggregation keys
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"))
    tariff_id = Column(Integer, ForeignKey("tariffs.id"))
    
    # Legacy fields for compatibility
    service_id = Column(Integer)
    partner_id = Column(Integer)
    nas_id = Column(Integer)
    login = Column(String(255), index=True)
    
    # Time period
    period_type = Column(String(20), default="daily", index=True)  # daily, weekly, monthly
    period_start = Column(DateTime(timezone=True), index=True)
    period_end = Column(DateTime(timezone=True), index=True)
    start_date = Column(DateTime(timezone=True), index=True)
    start_time = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True), index=True)
    end_time = Column(DateTime(timezone=True))
    
    # Aggregated metrics
    total_sessions = Column(Integer, default=0)
    in_bytes = Column(BigInteger, default=0)
    out_bytes = Column(BigInteger, default=0)
    total_bytes_in = Column(BigInteger, default=0)
    total_bytes_out = Column(BigInteger, default=0)
    total_session_time = Column(Integer, default=0)  # seconds
    time_on = Column(Integer, default=0)
    
    # Session quality metrics
    successful_sessions = Column(Integer, default=0)
    failed_sessions = Column(Integer, default=0)
    average_session_duration = Column(Integer, default=0)  # seconds
    
    # Peak usage tracking
    peak_concurrent_sessions = Column(Integer, default=0)
    peak_usage_time = Column(DateTime(timezone=True))
    peak_bytes_per_hour = Column(BigInteger, default=0)
    
    # FUP statistics
    fup_exceeded_sessions = Column(Integer, default=0)
    total_fup_limited_time = Column(Integer, default=0)  # seconds
    
    # Network details
    ipv4 = Column(INET)
    ipv6 = Column(INET)
    mac = Column(String(17))
    call_to = Column(String(50))
    port = Column(String(50))
    
    # Revenue and billing
    price = Column(DECIMAL(10, 4), default=0)
    total_revenue = Column(DECIMAL(10, 4), default=0)
    
    # Legacy fields
    last_change = Column(DateTime(timezone=True), server_default=func.now())
    type = Column(String(50), default="mikrotik_api")
    login_is = Column(String(20), default="user")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", foreign_keys=[customer_id])

    def __repr__(self):
        return f"<CustomerStatistics {self.login}: {self.period_type} {self.period_start}>"

    @property
    def total_bytes(self):
        """Total bytes transferred (in + out)"""
        return (self.in_bytes or 0) + (self.out_bytes or 0)

    @property
    def total_gb(self):
        """Total data in GB"""
        return round(self.total_bytes / (1024**3), 2)

    @property
    def average_session_hours(self):
        """Average session duration in hours"""
        return round((self.average_session_duration or 0) / 3600, 2)

    @property
    def session_duration_hours(self):
        """Session duration in hours"""
        return round((self.time_on or 0) / 3600, 2)

    @property
    def success_rate(self):
        """Session success rate as percentage"""
        if not self.total_sessions:
            return 0
        return round((self.successful_sessions / self.total_sessions) * 100, 1)


# Performance indexes
from sqlalchemy import Index

# RADIUS session indexes
Index('idx_radius_sessions_customer_active', RadiusSession.customer_id, RadiusSession.status)
Index('idx_radius_sessions_nas_time', RadiusSession.nas_device_id, RadiusSession.start_time)
Index('idx_radius_sessions_ip', RadiusSession.framed_ip_address)
Index('idx_radius_sessions_username', RadiusSession.username)
Index('idx_radius_sessions_session_type', RadiusSession.session_type)

# Interim update indexes
Index('idx_interim_updates_session_time', RADIUSInterimUpdate.radius_session_id, RADIUSInterimUpdate.update_time)

# Statistics indexes
Index('idx_session_stats_customer_period', CustomerStatistics.customer_id, CustomerStatistics.period_type, CustomerStatistics.period_start)
Index('idx_session_stats_nas_period', CustomerStatistics.nas_device_id, CustomerStatistics.period_type, CustomerStatistics.period_start)

# Online status indexes
Index('idx_online_status_ip', CustomerOnline.ipv4)
Index('idx_online_status_nas', CustomerOnline.nas_device_id)
