"""
NAS/RADIUS Module - Authentication Infrastructure

This module provides comprehensive Network Access Server (NAS) and RADIUS
authentication infrastructure management, independent of vendor implementations.

Core Principles:
- Vendor independence: Works with any RADIUS-compatible NAS device
- Protocol compliance: Full RADIUS RFC compliance
- Flexible authentication: Support for multiple auth methods and protocols
- Comprehensive accounting: Detailed session and usage tracking
- Scalable architecture: Support for distributed RADIUS infrastructure
"""

import enum

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class NASType(enum.Enum):
    """Network Access Server types"""

    MIKROTIK = "mikrotik"
    CISCO = "cisco"
    JUNIPER = "juniper"
    UBIQUITI = "ubiquiti"
    GENERIC = "generic"
    FREERADIUS = "freeradius"
    PFSENSE = "pfsense"


class AuthMethod(enum.Enum):
    """Authentication methods supported by NAS"""

    PPPOE = "pppoe"
    HOTSPOT = "hotspot"
    DOT1X = "dot1x"
    WIRELESS = "wireless"
    VPN = "vpn"
    DHCP = "dhcp"
    STATIC = "static"


class SessionStatus(enum.Enum):
    """RADIUS session status"""

    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"
    DISCONNECTED = "disconnected"


class AcctStatusType(enum.Enum):
    """RADIUS accounting status types (RFC 2866)"""

    START = "start"
    STOP = "stop"
    INTERIM_UPDATE = "interim_update"
    ACCOUNTING_ON = "accounting_on"
    ACCOUNTING_OFF = "accounting_off"


# Core NAS/RADIUS Models


class NASDevice(Base):
    """Network Access Server configuration - vendor agnostic"""

    __tablename__ = "nas_devices"

    id = Column(Integer, primary_key=True, index=True)

    # Device association
    device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)

    # NAS identification
    nas_identifier = Column(String(255), unique=True, nullable=False)
    nas_ip = Column(INET, nullable=False, unique=True)
    nas_type = Column(Enum(NASType), nullable=False)
    nas_port_type = Column(String(50))  # Ethernet, Wireless, etc.

    # RADIUS configuration
    radius_secret = Column(String(255), nullable=False)
    radius_server_id = Column(Integer, ForeignKey("radius_servers.id"))

    # Authentication configuration
    auth_methods = Column(ARRAY(String))  # Supported auth methods
    default_auth_method = Column(Enum(AuthMethod))

    # Accounting configuration
    accounting_enabled = Column(Boolean, default=True)
    interim_accounting = Column(Boolean, default=True)
    interim_interval = Column(Integer, default=300)  # seconds

    # Session management
    session_timeout = Column(Integer, default=0)  # 0 = no timeout
    idle_timeout = Column(Integer, default=0)
    max_sessions_per_user = Column(Integer, default=1)

    # Traffic shaping integration
    shaping_enabled = Column(Boolean, default=False)
    default_upload_limit = Column(Integer)  # kbps
    default_download_limit = Column(Integer)  # kbps

    # Status and monitoring
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime(timezone=True))
    status = Column(String(20), default="unknown")  # online, offline, error

    # Vendor-specific configuration
    vendor_config = Column(JSONB)  # Flexible vendor-specific settings

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("NetworkDevice")
    radius_server = relationship("RADIUSServer", back_populates="nas_devices")
    sessions = relationship("RADIUSSession", back_populates="nas_device")
    accounting_records = relationship("RADIUSAccounting", back_populates="nas_device")


class RADIUSServer(Base):
    """RADIUS server configuration and management"""

    __tablename__ = "radius_servers"

    id = Column(Integer, primary_key=True, index=True)

    # Server identification
    name = Column(String(255), nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(INET, nullable=False)

    # RADIUS configuration
    auth_port = Column(Integer, default=1812)
    acct_port = Column(Integer, default=1813)
    shared_secret = Column(String(255), nullable=False)

    # Server capabilities
    supports_authentication = Column(Boolean, default=True)
    supports_accounting = Column(Boolean, default=True)
    supports_coa = Column(Boolean, default=False)  # Change of Authorization
    coa_port = Column(Integer, default=3799)

    # Load balancing and failover
    priority = Column(Integer, default=100)
    weight = Column(Integer, default=1)
    is_backup = Column(Boolean, default=False)

    # Monitoring and health
    is_active = Column(Boolean, default=True)
    health_check_enabled = Column(Boolean, default=True)
    health_check_interval = Column(Integer, default=60)  # seconds
    last_health_check = Column(DateTime(timezone=True))
    response_time_ms = Column(Integer)

    # Statistics
    auth_requests_total = Column(BigInteger, default=0)
    auth_accepts_total = Column(BigInteger, default=0)
    auth_rejects_total = Column(BigInteger, default=0)
    acct_requests_total = Column(BigInteger, default=0)
    acct_responses_total = Column(BigInteger, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    nas_devices = relationship("NASDevice", back_populates="radius_server")


class RADIUSClient(Base):
    """RADIUS client configuration (legacy compatibility)"""

    __tablename__ = "radius_clients"

    id = Column(Integer, primary_key=True, index=True)

    # Client identification
    client_name = Column(String(255), nullable=False)
    client_ip = Column(INET, nullable=False, unique=True)
    client_mask = Column(Integer, default=32)  # CIDR mask

    # Authentication
    shared_secret = Column(String(255), nullable=False)

    # Client properties
    client_type = Column(String(50), default="nas")
    description = Column(Text)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RADIUSSession(Base):
    """Active RADIUS authentication sessions"""

    __tablename__ = "radius_sessions_modular"

    id = Column(Integer, primary_key=True, index=True)

    # Session identification
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"), nullable=False)

    # User identification
    username = Column(String(255), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # Session details
    nas_ip = Column(INET, nullable=False)
    nas_port = Column(String(50))
    nas_port_type = Column(String(50))
    service_type = Column(String(50))

    # Network assignment
    framed_ip = Column(INET, index=True)
    framed_netmask = Column(INET)
    framed_gateway = Column(INET)

    # Authentication details
    auth_method = Column(Enum(AuthMethod))
    calling_station_id = Column(String(50))  # MAC address or phone number
    called_station_id = Column(String(50))  # NAS identifier

    # Session timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    last_update = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True))
    session_duration = Column(Integer, default=0)  # seconds

    # Traffic accounting
    bytes_in = Column(BigInteger, default=0)
    bytes_out = Column(BigInteger, default=0)
    packets_in = Column(BigInteger, default=0)
    packets_out = Column(BigInteger, default=0)

    # Session limits and quotas
    session_timeout = Column(Integer)  # seconds
    idle_timeout = Column(Integer)  # seconds
    data_limit_bytes = Column(BigInteger)  # Data quota
    time_limit_seconds = Column(Integer)  # Time quota

    # Traffic shaping
    upload_limit_kbps = Column(Integer)
    download_limit_kbps = Column(Integer)
    upload_burst_kbps = Column(Integer)
    download_burst_kbps = Column(Integer)

    # Session status
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    terminate_cause = Column(String(100))  # Reason for termination

    # Additional attributes
    radius_attributes = Column(JSONB)  # Additional RADIUS attributes

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    nas_device = relationship("NASDevice", back_populates="sessions")
    customer = relationship("Customer", foreign_keys=[customer_id])
    accounting_records = relationship("RADIUSAccounting", back_populates="session")


class RADIUSAccounting(Base):
    """RADIUS accounting records (RFC 2866)"""

    __tablename__ = "radius_accounting"

    id = Column(Integer, primary_key=True, index=True)

    # Accounting identification
    radius_session_id = Column(
        Integer,
        ForeignKey("radius_sessions_modular.id", ondelete="CASCADE"),
        index=True,
    )
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"), nullable=False)

    # User identification
    username = Column(String(255), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # Accounting type
    acct_status_type = Column(Enum(AcctStatusType), nullable=False)
    acct_session_id = Column(String(255), nullable=False)
    acct_unique_id = Column(String(255), unique=True)

    # Network details
    nas_ip = Column(INET, nullable=False)
    nas_port = Column(String(50))
    framed_ip = Column(INET)

    # Traffic counters
    acct_input_octets = Column(BigInteger, default=0)
    acct_output_octets = Column(BigInteger, default=0)
    acct_input_packets = Column(BigInteger, default=0)
    acct_output_packets = Column(BigInteger, default=0)

    # Session timing
    acct_session_time = Column(Integer, default=0)  # seconds
    acct_delay_time = Column(Integer, default=0)

    # Termination details
    acct_terminate_cause = Column(String(100))
    acct_stop_delay = Column(Integer, default=0)

    # Additional accounting attributes
    calling_station_id = Column(String(50))
    called_station_id = Column(String(50))
    service_type = Column(String(50))

    # Custom attributes
    vendor_specific = Column(JSONB)  # Vendor-specific attributes

    # Record metadata
    record_timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    processed = Column(Boolean, default=False)
    billing_processed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship(
        "RADIUSSession",
        foreign_keys=[radius_session_id],
        back_populates="accounting_records",
    )
    nas_device = relationship("NASDevice", back_populates="accounting_records")
    customer = relationship("Customer", foreign_keys=[customer_id])


# RADIUS Authentication and Authorization


class RADIUSProfile(Base):
    """RADIUS user profiles and service definitions"""

    __tablename__ = "radius_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # Profile identification
    profile_name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    # Service parameters
    service_type = Column(String(50))  # Framed-User, Login-User, etc.
    framed_protocol = Column(String(50))  # PPP, SLIP, etc.

    # Network configuration
    framed_ip_pool = Column(String(255))  # IP pool name
    framed_netmask = Column(INET)
    framed_gateway = Column(INET)
    dns_servers = Column(ARRAY(String))

    # Session limits
    session_timeout = Column(Integer, default=0)
    idle_timeout = Column(Integer, default=0)
    max_concurrent_sessions = Column(Integer, default=1)

    # Traffic shaping
    upload_limit_kbps = Column(Integer)
    download_limit_kbps = Column(Integer)
    upload_burst_kbps = Column(Integer)
    download_burst_kbps = Column(Integer)
    burst_threshold_kbps = Column(Integer)
    burst_time_seconds = Column(Integer)

    # Data quotas
    daily_data_limit_mb = Column(Integer)
    monthly_data_limit_mb = Column(Integer)
    total_data_limit_mb = Column(Integer)

    # Time quotas
    daily_time_limit_minutes = Column(Integer)
    monthly_time_limit_minutes = Column(Integer)
    total_time_limit_minutes = Column(Integer)

    # Access control
    allowed_nas_devices = Column(ARRAY(Integer))  # Restrict to specific NAS devices
    allowed_time_ranges = Column(JSONB)  # Time-based access control
    allowed_calling_stations = Column(ARRAY(String))  # MAC address restrictions

    # RADIUS attributes
    reply_attributes = Column(JSONB)  # RADIUS reply attributes
    check_attributes = Column(JSONB)  # RADIUS check attributes

    # Profile status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user_profiles = relationship("RADIUSUserProfile", back_populates="profile")


class RADIUSUserProfile(Base):
    """Association between users and RADIUS profiles"""

    __tablename__ = "radius_user_profiles"

    id = Column(Integer, primary_key=True, index=True)

    # User association
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("radius_profiles.id"), nullable=False)

    # Assignment details
    assigned_by = Column(Integer, ForeignKey("administrators.id"))
    assignment_reason = Column(String(255))

    # Override settings
    override_session_timeout = Column(Integer)
    override_data_limit_mb = Column(Integer)
    override_upload_limit_kbps = Column(Integer)
    override_download_limit_kbps = Column(Integer)

    # Status
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime(timezone=True))
    effective_until = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer")
    profile = relationship("RADIUSProfile", back_populates="user_profiles")


# RADIUS Monitoring and Analytics


class RADIUSStatistics(Base):
    """RADIUS server and NAS statistics"""

    __tablename__ = "radius_statistics"

    id = Column(Integer, primary_key=True, index=True)

    # Statistics scope
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"))
    radius_server_id = Column(Integer, ForeignKey("radius_servers.id"))

    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20))  # hourly, daily, weekly, monthly

    # Authentication statistics
    auth_requests = Column(Integer, default=0)
    auth_accepts = Column(Integer, default=0)
    auth_rejects = Column(Integer, default=0)
    auth_challenges = Column(Integer, default=0)

    # Accounting statistics
    acct_requests = Column(Integer, default=0)
    acct_responses = Column(Integer, default=0)
    acct_start_records = Column(Integer, default=0)
    acct_stop_records = Column(Integer, default=0)
    acct_update_records = Column(Integer, default=0)

    # Session statistics
    total_sessions = Column(Integer, default=0)
    active_sessions = Column(Integer, default=0)
    peak_concurrent_sessions = Column(Integer, default=0)
    average_session_duration = Column(Integer, default=0)  # seconds

    # Traffic statistics
    total_bytes_in = Column(BigInteger, default=0)
    total_bytes_out = Column(BigInteger, default=0)
    peak_throughput_bps = Column(BigInteger, default=0)
    average_throughput_bps = Column(BigInteger, default=0)

    # Performance metrics
    average_response_time_ms = Column(Integer, default=0)
    timeout_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    nas_device = relationship("NASDevice")
    radius_server = relationship("RADIUSServer")


class RADIUSAlert(Base):
    """RADIUS-specific alerts and monitoring"""

    __tablename__ = "radius_alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Alert scope
    nas_device_id = Column(Integer, ForeignKey("nas_devices.id"))
    radius_server_id = Column(Integer, ForeignKey("radius_servers.id"))

    # Alert details
    alert_type = Column(
        String(50), nullable=False
    )  # server_down, high_reject_rate, session_limit
    severity = Column(String(20), nullable=False)  # critical, warning, info
    title = Column(String(255), nullable=False)
    message = Column(Text)

    # Alert context
    threshold_value = Column(String(100))
    current_value = Column(String(100))
    metric_name = Column(String(100))

    # Alert lifecycle
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("administrators.id"))
    acknowledged_at = Column(DateTime(timezone=True))

    # Auto-resolution
    auto_resolve = Column(Boolean, default=True)
    resolution_threshold = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    last_occurrence = Column(DateTime(timezone=True))
    occurrence_count = Column(Integer, default=1)

    # Relationships
    nas_device = relationship("NASDevice")
    radius_server = relationship("RADIUSServer")
