"""
MikroTik Integration Module - Vendor-Specific Implementation

This module provides MikroTik-specific configuration and management functionality,
extending the core network models with RouterOS-specific features.

Core Principles:
- Extends core network models: Links to NetworkDevice via device_id
- RouterOS API integration: Native API support for configuration management
- Queue management: Simple Queue and Queue Tree support
- Firewall integration: Address lists, filter rules, NAT rules
- User management: Hotspot users, PPPoE secrets, DHCP leases
- Monitoring integration: SNMP, Torch, bandwidth monitoring
"""

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class RouterOSVersion(enum.Enum):
    """RouterOS version categories"""

    V6 = "v6"
    V7 = "v7"
    UNKNOWN = "unknown"


class QueueType(enum.Enum):
    """MikroTik queue types"""

    SIMPLE_QUEUE = "simple_queue"
    QUEUE_TREE = "queue_tree"
    INTERFACE_QUEUE = "interface_queue"


class FirewallAction(enum.Enum):
    """MikroTik firewall actions"""

    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    RETURN = "return"
    JUMP = "jump"
    LOG = "log"
    PASSTHROUGH = "passthrough"


# Core MikroTik Device Configuration


class MikroTikDevice(Base):
    """MikroTik-specific device configuration and management"""

    __tablename__ = "mikrotik_devices"

    # Primary key links to core NetworkDevice
    device_id = Column(Integer, ForeignKey("network_devices.id"), primary_key=True)

    # RouterOS Information
    routeros_version = Column(String(100))
    routeros_version_category = Column(
        Enum(RouterOSVersion), default=RouterOSVersion.UNKNOWN
    )
    architecture = Column(String(50))  # x86, arm, mipsbe, etc.
    board_name = Column(String(100))
    license_level = Column(String(50))  # free, p1, p-unlimited, etc.

    # API Configuration
    api_enabled = Column(Boolean, default=False)
    api_username = Column(String(100))
    api_password = Column(String(255))  # Encrypted
    api_port = Column(Integer, default=8728)
    api_ssl_enabled = Column(Boolean, default=False)
    api_ssl_port = Column(Integer, default=8729)

    # SSH Configuration
    ssh_enabled = Column(Boolean, default=True)
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String(100))
    ssh_password = Column(String(255))  # Encrypted

    # SNMP Configuration
    snmp_enabled = Column(Boolean, default=False)
    snmp_community = Column(String(100), default="public")
    snmp_version = Column(String(10), default="v2c")  # v1, v2c, v3
    snmp_port = Column(Integer, default=161)

    # System Information
    cpu_count = Column(Integer)
    cpu_frequency = Column(Integer)  # MHz
    total_memory = Column(Integer)  # MB
    total_storage = Column(Integer)  # MB

    # Network Configuration
    identity = Column(String(255))  # RouterOS identity
    default_gateway = Column(INET)
    dns_servers = Column(ARRAY(String))
    ntp_servers = Column(ARRAY(String))
    timezone = Column(String(100))

    # Feature Capabilities
    supports_hotspot = Column(Boolean, default=False)
    supports_pppoe_server = Column(Boolean, default=False)
    supports_vpn = Column(Boolean, default=False)
    supports_wireless = Column(Boolean, default=False)
    supports_routing = Column(Boolean, default=False)

    # Management Status
    last_api_connection = Column(DateTime(timezone=True))
    last_config_backup = Column(DateTime(timezone=True))
    api_connection_errors = Column(Integer, default=0)
    is_managed = Column(Boolean, default=True)

    # Monitoring Configuration
    monitoring_enabled = Column(Boolean, default=True)
    monitoring_interval = Column(Integer, default=300)  # seconds
    collect_interface_stats = Column(Boolean, default=True)
    collect_queue_stats = Column(Boolean, default=True)
    collect_system_stats = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True))

    # Relationships
    device = relationship("NetworkDevice")
    interfaces = relationship("MikroTikInterface", back_populates="mikrotik_device")
    simple_queues = relationship(
        "MikroTikSimpleQueue", back_populates="mikrotik_device"
    )
    firewall_rules = relationship(
        "MikroTikFirewallRule", back_populates="mikrotik_device"
    )
    address_lists = relationship(
        "MikroTikAddressList", back_populates="mikrotik_device"
    )
    pppoe_secrets = relationship(
        "MikroTikPPPoESecret", back_populates="mikrotik_device"
    )
    hotspot_users = relationship(
        "MikroTikHotspotUser", back_populates="mikrotik_device"
    )
    dhcp_leases = relationship("MikroTikDHCPLease", back_populates="mikrotik_device")


class MikroTikInterface(Base):
    """MikroTik network interfaces"""

    __tablename__ = "mikrotik_interfaces"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # Interface identification
    interface_name = Column(String(100), nullable=False)
    interface_type = Column(String(50))  # ether, wlan, bridge, vlan, pppoe-out, etc.
    default_name = Column(String(100))  # Default RouterOS name

    # Physical properties
    mac_address = Column(String(17))
    mtu = Column(Integer, default=1500)

    # Network configuration
    ip_addresses = Column(ARRAY(String))  # Can have multiple IPs
    network_mask = Column(String(20))
    gateway = Column(INET)

    # Interface status
    is_enabled = Column(Boolean, default=True)
    is_running = Column(Boolean, default=False)
    link_speed = Column(String(20))  # 1Gbps, 100Mbps, etc.
    duplex = Column(String(10))  # full, half

    # Traffic statistics
    rx_bytes = Column(Integer, default=0)
    tx_bytes = Column(Integer, default=0)
    rx_packets = Column(Integer, default=0)
    tx_packets = Column(Integer, default=0)
    rx_errors = Column(Integer, default=0)
    tx_errors = Column(Integer, default=0)

    # Wireless-specific (if applicable)
    wireless_mode = Column(String(50))  # ap-bridge, station, etc.
    wireless_ssid = Column(String(100))
    wireless_frequency = Column(String(20))
    wireless_channel = Column(String(10))
    wireless_signal_strength = Column(Integer)

    # VLAN configuration
    vlan_id = Column(Integer)
    vlan_parent_interface = Column(String(100))

    # Bridge configuration
    bridge_name = Column(String(100))
    is_bridge_port = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_stats_update = Column(DateTime(timezone=True))

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="interfaces")


# Traffic Management and QoS


class MikroTikSimpleQueue(Base):
    """MikroTik Simple Queue management"""

    __tablename__ = "mikrotik_simple_queues"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # Queue identification
    queue_name = Column(String(255), nullable=False)
    queue_id = Column(String(50))  # RouterOS internal ID

    # Target configuration
    target_ip = Column(INET)
    target_network = Column(INET)  # For network-based queues
    target_interface = Column(String(100))

    # Customer association
    customer_id = Column(Integer, ForeignKey("customers.id"))
    service_id = Column(Integer)  # Link to service assignment

    # Speed limits (in bits per second)
    max_limit_upload = Column(Integer)  # bps
    max_limit_download = Column(Integer)  # bps

    # Burst configuration
    burst_limit_upload = Column(Integer)  # bps
    burst_limit_download = Column(Integer)  # bps
    burst_threshold_upload = Column(Integer)  # bps
    burst_threshold_download = Column(Integer)  # bps
    burst_time = Column(Integer, default=8)  # seconds

    # Priority and limits
    priority = Column(Integer, default=8)  # 1-8, lower is higher priority
    limit_at_upload = Column(Integer)  # Guaranteed bandwidth
    limit_at_download = Column(Integer)

    # Queue status
    is_enabled = Column(Boolean, default=True)
    is_dynamic = Column(Boolean, default=False)  # Created automatically

    # Traffic statistics
    bytes_upload = Column(Integer, default=0)
    bytes_download = Column(Integer, default=0)
    packets_upload = Column(Integer, default=0)
    packets_download = Column(Integer, default=0)

    # Queue tree association
    parent_queue = Column(String(255))
    queue_tree_upload = Column(String(255))
    queue_tree_download = Column(String(255))

    # Additional configuration
    comment = Column(Text)
    disabled = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_stats_update = Column(DateTime(timezone=True))

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="simple_queues")
    customer = relationship("Customer", foreign_keys=[customer_id])


# Firewall and Security


class MikroTikFirewallRule(Base):
    """MikroTik firewall filter rules"""

    __tablename__ = "mikrotik_firewall_rules"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # Rule identification
    rule_id = Column(String(50))  # RouterOS internal ID
    chain = Column(String(50), nullable=False)  # input, forward, output

    # Rule position and grouping
    rule_order = Column(Integer, default=0)
    rule_comment = Column(Text)

    # Match criteria
    protocol = Column(String(20))  # tcp, udp, icmp, etc.
    src_address = Column(INET)
    src_port = Column(String(100))  # Can be range like "80-90"
    dst_address = Column(INET)
    dst_port = Column(String(100))

    # Interface matching
    in_interface = Column(String(100))
    out_interface = Column(String(100))
    in_interface_list = Column(String(100))
    out_interface_list = Column(String(100))

    # Address list matching
    src_address_list = Column(String(100))
    dst_address_list = Column(String(100))

    # Connection state
    connection_state = Column(String(100))  # new, established, related, invalid
    connection_nat_state = Column(String(100))

    # Action configuration
    action = Column(Enum(FirewallAction), nullable=False)
    jump_target = Column(String(100))  # For jump action
    log_prefix = Column(String(100))  # For log action

    # Rule status
    is_enabled = Column(Boolean, default=True)
    is_dynamic = Column(Boolean, default=False)

    # Statistics
    packet_count = Column(Integer, default=0)
    byte_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="firewall_rules")


class MikroTikAddressList(Base):
    """MikroTik firewall address lists"""

    __tablename__ = "mikrotik_address_lists"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # Address list entry
    list_name = Column(String(100), nullable=False)
    address = Column(INET, nullable=False)

    # Entry properties
    comment = Column(Text)
    timeout = Column(String(50))  # Timeout specification

    # Customer association
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # Entry status
    is_dynamic = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="address_lists")
    customer = relationship("Customer", foreign_keys=[customer_id])


# User Management


class MikroTikPPPoESecret(Base):
    """MikroTik PPPoE server secrets"""

    __tablename__ = "mikrotik_pppoe_secrets"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # PPPoE credentials
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)

    # Customer association
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_id = Column(Integer)  # Link to service assignment

    # Network configuration
    local_address = Column(INET)  # Server-side IP
    remote_address = Column(INET)  # Client-side IP
    profile = Column(String(100))  # PPP profile name

    # Service configuration
    service = Column(String(50), default="pppoe")
    caller_id = Column(String(50))  # MAC address restriction

    # Limits and restrictions
    rate_limit = Column(String(100))  # Format: "upload/download"
    session_timeout = Column(String(50))
    idle_timeout = Column(String(50))

    # Status
    is_disabled = Column(Boolean, default=False)
    comment = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="pppoe_secrets")
    customer = relationship("Customer", foreign_keys=[customer_id])


class MikroTikHotspotUser(Base):
    """MikroTik Hotspot user management"""

    __tablename__ = "mikrotik_hotspot_users"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # Hotspot credentials
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)

    # Customer association
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # User configuration
    profile = Column(String(100))  # Hotspot profile
    server = Column(String(100))  # Hotspot server name

    # Limits and quotas
    limit_uptime = Column(String(50))  # Time limit
    limit_bytes_in = Column(Integer)  # Upload limit
    limit_bytes_out = Column(Integer)  # Download limit
    limit_bytes_total = Column(Integer)  # Total traffic limit

    # User properties
    address = Column(INET)  # Assigned IP address
    mac_address = Column(String(17))  # MAC address binding
    email = Column(String(255))
    phone = Column(String(50))

    # Status
    is_disabled = Column(Boolean, default=False)
    comment = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="hotspot_users")
    customer = relationship("Customer", foreign_keys=[customer_id])


class MikroTikDHCPLease(Base):
    """MikroTik DHCP server leases"""

    __tablename__ = "mikrotik_dhcp_leases"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # Lease identification
    mac_address = Column(String(17), nullable=False)
    ip_address = Column(INET, nullable=False)

    # DHCP server configuration
    server_name = Column(String(100))  # DHCP server name

    # Lease properties
    hostname = Column(String(255))
    client_id = Column(String(255))

    # Customer association
    customer_id = Column(Integer, ForeignKey("customers.id"))

    # Lease timing
    lease_time = Column(String(50))  # Lease duration
    expires_after = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True))

    # Lease status
    status = Column(String(20))  # bound, waiting, offered
    is_static = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)

    # Additional properties
    rate_limit = Column(String(100))
    comment = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mikrotik_device = relationship("MikroTikDevice", back_populates="dhcp_leases")
    customer = relationship("Customer", foreign_keys=[customer_id])


# Monitoring and Statistics


class MikroTikSystemStats(Base):
    """MikroTik system performance statistics"""

    __tablename__ = "mikrotik_system_stats"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )

    # System metrics
    cpu_load = Column(Float)  # CPU usage percentage
    memory_usage = Column(Integer)  # Used memory in MB
    memory_total = Column(Integer)  # Total memory in MB
    storage_usage = Column(Integer)  # Used storage in MB
    storage_total = Column(Integer)  # Total storage in MB

    # Network metrics
    uptime = Column(Integer)  # Uptime in seconds
    voltage = Column(Float)  # Power supply voltage
    temperature = Column(Float)  # System temperature (Celsius)

    # Interface summary
    total_interfaces = Column(Integer, default=0)
    active_interfaces = Column(Integer, default=0)

    # Connection summary
    total_connections = Column(Integer, default=0)
    tcp_connections = Column(Integer, default=0)
    udp_connections = Column(Integer, default=0)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    mikrotik_device = relationship("MikroTikDevice")


class MikroTikInterfaceStats(Base):
    """MikroTik interface traffic statistics"""

    __tablename__ = "mikrotik_interface_stats"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(
        Integer, ForeignKey("mikrotik_devices.device_id"), nullable=False
    )
    interface_name = Column(String(100), nullable=False)

    # Traffic counters
    rx_bytes = Column(Integer, default=0)
    tx_bytes = Column(Integer, default=0)
    rx_packets = Column(Integer, default=0)
    tx_packets = Column(Integer, default=0)

    # Error counters
    rx_errors = Column(Integer, default=0)
    tx_errors = Column(Integer, default=0)
    rx_drops = Column(Integer, default=0)
    tx_drops = Column(Integer, default=0)

    # Rate calculations (per second)
    rx_rate_bps = Column(Integer, default=0)
    tx_rate_bps = Column(Integer, default=0)
    rx_rate_pps = Column(Integer, default=0)
    tx_rate_pps = Column(Integer, default=0)

    # Interface status
    is_running = Column(Boolean, default=False)
    link_speed = Column(String(20))

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    mikrotik_device = relationship("MikroTikDevice")
