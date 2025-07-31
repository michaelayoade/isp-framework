"""
Cisco Integration Module - Vendor-Specific Implementation

This module provides Cisco-specific configuration and management functionality,
extending the core network models with IOS/IOS-XE/NX-OS specific features.

Core Principles:
- Extends core network models: Links to NetworkDevice via device_id
- Multi-platform support: IOS, IOS-XE, IOS-XR, NX-OS
- CLI and NETCONF integration: Traditional CLI and modern NETCONF/YANG
- Enterprise features: VRF, MPLS, BGP, OSPF configuration
- Security integration: AAA, 802.1X, TrustSec
"""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CiscoPlatform(enum.Enum):
    """Cisco platform types"""

    IOS = "ios"
    IOS_XE = "ios_xe"
    IOS_XR = "ios_xr"
    NX_OS = "nx_os"
    ASA = "asa"
    UNKNOWN = "unknown"


class InterfaceType(enum.Enum):
    """Cisco interface types"""

    GIGABIT_ETHERNET = "GigabitEthernet"
    FAST_ETHERNET = "FastEthernet"
    TEN_GIGABIT_ETHERNET = "TenGigabitEthernet"
    SERIAL = "Serial"
    LOOPBACK = "Loopback"
    VLAN = "Vlan"
    TUNNEL = "Tunnel"
    PORT_CHANNEL = "Port-channel"


class CiscoDevice(Base):
    """Cisco-specific device configuration and management"""

    __tablename__ = "cisco_devices"

    # Primary key links to core NetworkDevice
    device_id = Column(Integer, ForeignKey("network_devices.id"), primary_key=True)

    # Platform Information
    platform = Column(Enum(CiscoPlatform), default=CiscoPlatform.UNKNOWN)
    ios_version = Column(String(100))
    hardware_model = Column(String(100))
    processor_type = Column(String(100))
    total_memory = Column(Integer)  # KB

    # Management Access
    enable_password = Column(String(255))  # Encrypted
    enable_secret = Column(String(255))  # Encrypted
    console_password = Column(String(255))  # Encrypted
    vty_password = Column(String(255))  # Encrypted

    # SSH Configuration
    ssh_enabled = Column(Boolean, default=True)
    ssh_version = Column(String(10), default="2")
    ssh_timeout = Column(Integer, default=60)

    # SNMP Configuration
    snmp_enabled = Column(Boolean, default=False)
    snmp_community_ro = Column(String(100), default="public")
    snmp_community_rw = Column(String(100))
    snmp_version = Column(String(10), default="v2c")
    snmp_contact = Column(String(255))
    snmp_location = Column(String(255))

    # AAA Configuration
    aaa_enabled = Column(Boolean, default=False)
    tacacs_servers = Column(ARRAY(String))
    radius_servers = Column(ARRAY(String))
    local_users = Column(JSONB)  # Local user accounts

    # Network Services
    cdp_enabled = Column(Boolean, default=True)
    lldp_enabled = Column(Boolean, default=False)
    spanning_tree_mode = Column(String(20))  # pvst, rapid-pvst, mst

    # Routing Configuration
    routing_enabled = Column(Boolean, default=True)
    routing_protocols = Column(ARRAY(String))  # ospf, eigrp, bgp, rip

    # Feature Capabilities
    supports_vrf = Column(Boolean, default=False)
    supports_mpls = Column(Boolean, default=False)
    supports_qos = Column(Boolean, default=False)
    supports_ipsec = Column(Boolean, default=False)

    # Management Status
    last_config_sync = Column(DateTime(timezone=True))
    config_drift_detected = Column(Boolean, default=False)
    compliance_status = Column(String(20), default="unknown")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("NetworkDevice")
    interfaces = relationship("CiscoInterface", back_populates="cisco_device")
    vlans = relationship("CiscoVLAN", back_populates="cisco_device")
    access_lists = relationship("CiscoAccessList", back_populates="cisco_device")


class CiscoInterface(Base):
    """Cisco network interfaces with IOS-specific configuration"""

    __tablename__ = "cisco_interfaces"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("cisco_devices.device_id"), nullable=False)

    # Interface identification
    interface_name = Column(String(100), nullable=False)  # e.g., "GigabitEthernet0/1"
    interface_type = Column(Enum(InterfaceType))
    interface_number = Column(String(20))  # e.g., "0/1", "1/0/1"

    # Interface configuration
    description = Column(String(255))
    ip_address = Column(INET)
    subnet_mask = Column(INET)
    secondary_ips = Column(ARRAY(String))  # Secondary IP addresses

    # Layer 2 configuration
    switchport_mode = Column(String(20))  # access, trunk, dynamic
    access_vlan = Column(Integer)
    trunk_vlans = Column(String(255))  # VLAN ranges for trunk ports
    native_vlan = Column(Integer)

    # Physical properties
    speed = Column(String(20))  # auto, 10, 100, 1000
    duplex = Column(String(10))  # auto, full, half
    mtu = Column(Integer, default=1500)

    # Status
    administrative_status = Column(String(20), default="up")  # up, down
    operational_status = Column(String(20), default="down")  # up, down

    # Security features
    port_security_enabled = Column(Boolean, default=False)
    max_mac_addresses = Column(Integer, default=1)
    violation_action = Column(String(20))  # protect, restrict, shutdown

    # QoS configuration
    qos_policy_in = Column(String(100))
    qos_policy_out = Column(String(100))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cisco_device = relationship("CiscoDevice", back_populates="interfaces")


class CiscoVLAN(Base):
    """Cisco VLAN configuration"""

    __tablename__ = "cisco_vlans"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("cisco_devices.device_id"), nullable=False)

    # VLAN identification
    vlan_id = Column(Integer, nullable=False)
    vlan_name = Column(String(100), nullable=False)

    # VLAN properties
    status = Column(String(20), default="active")  # active, suspend
    mtu = Column(Integer, default=1500)

    # STP configuration
    stp_priority = Column(Integer, default=32768)
    stp_root_guard = Column(Boolean, default=False)
    stp_bpdu_guard = Column(Boolean, default=False)

    # IP configuration (for SVI)
    ip_address = Column(INET)
    subnet_mask = Column(INET)
    ip_helper_addresses = Column(ARRAY(String))  # DHCP relay

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cisco_device = relationship("CiscoDevice", back_populates="vlans")


class CiscoAccessList(Base):
    """Cisco Access Control Lists (ACLs)"""

    __tablename__ = "cisco_access_lists"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("cisco_devices.device_id"), nullable=False)

    # ACL identification
    acl_name = Column(String(100))
    acl_number = Column(Integer)  # For numbered ACLs
    acl_type = Column(String(20))  # standard, extended, named

    # ACL entry
    sequence_number = Column(Integer)
    action = Column(String(10))  # permit, deny

    # Match criteria
    protocol = Column(String(20))  # ip, tcp, udp, icmp, etc.
    source_address = Column(INET)
    source_wildcard = Column(INET)
    source_port = Column(String(50))
    destination_address = Column(INET)
    destination_wildcard = Column(INET)
    destination_port = Column(String(50))

    # Additional options
    established = Column(Boolean, default=False)
    log = Column(Boolean, default=False)
    time_range = Column(String(100))

    # Statistics
    match_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    cisco_device = relationship("CiscoDevice", back_populates="access_lists")
