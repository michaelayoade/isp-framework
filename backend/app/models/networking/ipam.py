"""
IPAM Module - IP Address Management

This module provides comprehensive IP address management functionality,
independent of network devices and vendor-specific implementations.

Core Principles:
- Device independence: IP management separate from physical infrastructure
- Hierarchical organization: Supernets, subnets, and individual IPs
- Flexible allocation: Support for static, DHCP, PPPoE, and other allocation methods
- Multi-tenancy: Support for customer, infrastructure, and management IP spaces
- IPv4/IPv6 dual-stack: Native support for both IP versions
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import INET, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class IPVersion(enum.Enum):
    """IP version enumeration"""
    IPV4 = 4
    IPV6 = 6


class PoolType(enum.Enum):
    """IP pool usage types"""
    CUSTOMER = "customer"           # Customer assignments
    INFRASTRUCTURE = "infrastructure"  # Network device management
    MANAGEMENT = "management"       # Out-of-band management
    TRANSIT = "transit"            # Inter-site connections
    LOOPBACK = "loopback"          # Device loopbacks
    POINT_TO_POINT = "point_to_point"  # P2P links
    DHCP = "dhcp"                  # DHCP pools
    RESERVED = "reserved"          # Reserved/future use


class AllocationStatus(enum.Enum):
    """IP allocation status"""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    QUARANTINED = "quarantined"    # Temporarily unusable
    DEPRECATED = "deprecated"      # Being phased out


class AllocationType(enum.Enum):
    """IP allocation methods"""
    STATIC = "static"              # Manually assigned
    DHCP = "dhcp"                  # DHCP reservation
    PPPOE = "pppoe"               # PPPoE assignment
    AUTOMATIC = "automatic"        # System-assigned
    TEMPORARY = "temporary"        # Temporary assignment


# Core IPAM Models

class IPPool(Base):
    """IPv4/IPv6 network pools - hierarchical IP space management"""
    __tablename__ = "ip_pools"

    id = Column(Integer, primary_key=True, index=True)
    
    # Network definition
    network = Column(INET, nullable=False, index=True)
    prefix_length = Column(Integer, nullable=False)
    ip_version = Column(Enum(IPVersion), nullable=False)
    
    # Pool identification
    name = Column(String(255), nullable=False)
    description = Column(Text)
    pool_type = Column(Enum(PoolType), nullable=False)
    
    # Hierarchical organization
    parent_pool_id = Column(Integer, ForeignKey("ip_pools.id"))
    is_supernet = Column(Boolean, default=False)
    
    # Geographic/organizational assignment
    site_id = Column(Integer, ForeignKey("network_sites.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    organization_unit = Column(String(255))  # Department, division, etc.
    
    # Pool configuration
    gateway_ip = Column(INET)
    dns_servers = Column(ARRAY(String))  # DNS server IPs
    domain_name = Column(String(255))
    lease_time = Column(Integer)  # DHCP lease time in seconds
    
    # Allocation settings
    auto_assign_gateway = Column(Boolean, default=True)
    auto_assign_dns = Column(Boolean, default=True)
    allow_split = Column(Boolean, default=True)  # Can be subdivided
    
    # Utilization tracking
    total_addresses = Column(Integer, default=0)
    allocated_addresses = Column(Integer, default=0)
    reserved_addresses = Column(Integer, default=0)
    utilization_threshold_warning = Column(Integer, default=80)  # Percentage
    utilization_threshold_critical = Column(Integer, default=95)
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True)
    is_deprecated = Column(Boolean, default=False)
    deprecation_date = Column(DateTime(timezone=True))
    
    # VLAN association
    vlan_id = Column(Integer)
    vlan_name = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent_pool = relationship("IPPool", remote_side=[id])
    child_pools = relationship("IPPool", back_populates="parent_pool")
    ip_allocations = relationship("IPAllocation", back_populates="pool")
    dhcp_reservations = relationship("DHCPReservation", back_populates="pool")


class IPAllocation(Base):
    """Individual IP address assignments"""
    __tablename__ = "ip_allocations"

    id = Column(Integer, primary_key=True, index=True)
    
    # IP assignment
    pool_id = Column(Integer, ForeignKey("ip_pools.id"), nullable=False)
    ip_address = Column(INET, nullable=False, index=True)
    
    # Assignment details
    hostname = Column(String(255))
    description = Column(Text)
    allocation_type = Column(Enum(AllocationType), nullable=False)
    status = Column(Enum(AllocationStatus), nullable=False, default=AllocationStatus.ALLOCATED)
    
    # Assignment targets (flexible references)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    device_id = Column(Integer, ForeignKey("network_devices.id"))
    service_id = Column(Integer)  # Generic service reference
    
    # Network configuration
    subnet_mask = Column(INET)  # For IPv4
    gateway_ip = Column(INET)
    dns_servers = Column(ARRAY(String))
    domain_name = Column(String(255))
    
    # MAC address binding (for DHCP/static assignments)
    mac_address = Column(String(17))  # MAC address format: XX:XX:XX:XX:XX:XX
    
    # Lease information (for DHCP)
    lease_start = Column(DateTime(timezone=True))
    lease_end = Column(DateTime(timezone=True))
    lease_duration = Column(Integer)  # seconds
    
    # Assignment metadata
    assigned_by = Column(Integer, ForeignKey("administrators.id"))
    assignment_reason = Column(String(255))
    
    # Status tracking
    last_seen = Column(DateTime(timezone=True))
    is_pingable = Column(Boolean)
    last_ping_check = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    allocated_at = Column(DateTime(timezone=True), server_default=func.now())
    released_at = Column(DateTime(timezone=True))

    # Relationships
    pool = relationship("IPPool", back_populates="ip_allocations")
    customer = relationship("Customer", foreign_keys=[customer_id])
    device = relationship("NetworkDevice", foreign_keys=[device_id])


class DHCPReservation(Base):
    """DHCP reservations and static assignments"""
    __tablename__ = "dhcp_reservations"

    id = Column(Integer, primary_key=True, index=True)
    
    # DHCP server association
    pool_id = Column(Integer, ForeignKey("ip_pools.id"), nullable=False)
    dhcp_server_id = Column(Integer, ForeignKey("network_devices.id"))
    
    # Reservation details
    mac_address = Column(String(17), nullable=False, index=True)
    ip_address = Column(INET, nullable=False)
    hostname = Column(String(255))
    
    # Client identification
    client_id = Column(String(255))  # DHCP client identifier
    customer_id = Column(Integer, ForeignKey("customers.id"))
    device_description = Column(String(255))
    
    # DHCP options
    lease_time = Column(Integer)  # Override pool default
    gateway_override = Column(INET)
    dns_override = Column(ARRAY(String))
    domain_override = Column(String(255))
    
    # Additional DHCP options (vendor-specific)
    dhcp_options = Column(JSONB)  # Flexible option storage
    
    # Reservation status
    is_active = Column(Boolean, default=True)
    is_static = Column(Boolean, default=False)  # Static vs dynamic reservation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pool = relationship("IPPool", back_populates="dhcp_reservations")
    dhcp_server = relationship("NetworkDevice", foreign_keys=[dhcp_server_id])
    customer = relationship("Customer", foreign_keys=[customer_id])


class IPRange(Base):
    """Contiguous IP address ranges within pools"""
    __tablename__ = "ip_ranges"

    id = Column(Integer, primary_key=True, index=True)
    
    # Range definition
    pool_id = Column(Integer, ForeignKey("ip_pools.id"), nullable=False)
    start_ip = Column(INET, nullable=False)
    end_ip = Column(INET, nullable=False)
    
    # Range properties
    name = Column(String(255))
    description = Column(Text)
    range_type = Column(Enum(PoolType))  # Purpose of this range
    
    # Range configuration
    is_assignable = Column(Boolean, default=True)
    auto_assign = Column(Boolean, default=False)
    priority = Column(Integer, default=100)  # Assignment priority
    
    # Utilization
    total_addresses = Column(Integer, default=0)
    allocated_addresses = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pool = relationship("IPPool")


class IPAMHistory(Base):
    """IP allocation history and audit trail"""
    __tablename__ = "ipam_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Historical record
    ip_address = Column(INET, nullable=False, index=True)
    pool_id = Column(Integer, ForeignKey("ip_pools.id"))
    
    # Action details
    action = Column(String(50), nullable=False)  # allocated, released, reserved, modified
    previous_status = Column(String(50))
    new_status = Column(String(50))
    
    # Assignment details
    customer_id = Column(Integer, ForeignKey("customers.id"))
    device_id = Column(Integer, ForeignKey("network_devices.id"))
    hostname = Column(String(255))
    mac_address = Column(String(17))
    
    # Change metadata
    changed_by = Column(Integer, ForeignKey("administrators.id"))
    change_reason = Column(String(255))
    additional_data = Column(JSONB)  # Flexible data storage
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    pool = relationship("IPPool")
    customer = relationship("Customer", foreign_keys=[customer_id])
    device = relationship("NetworkDevice", foreign_keys=[device_id])


# IP Scanning and Discovery

class IPScanResult(Base):
    """IP address scanning and discovery results"""
    __tablename__ = "ip_scan_results"

    id = Column(Integer, primary_key=True, index=True)
    
    # Scan details
    pool_id = Column(Integer, ForeignKey("ip_pools.id"), nullable=False)
    ip_address = Column(INET, nullable=False)
    scan_type = Column(String(50))  # ping, arp, snmp, port_scan
    
    # Scan results
    is_responsive = Column(Boolean, default=False)
    response_time_ms = Column(Integer)
    mac_address = Column(String(17))
    hostname = Column(String(255))
    
    # Device identification
    device_vendor = Column(String(100))  # From MAC OUI lookup
    device_type = Column(String(100))    # Detected device type
    operating_system = Column(String(100))
    
    # SNMP discovery (if available)
    snmp_community = Column(String(100))
    snmp_sysname = Column(String(255))
    snmp_sysdescr = Column(Text)
    snmp_contact = Column(String(255))
    snmp_location = Column(String(255))
    
    # Port scan results
    open_ports = Column(ARRAY(Integer))
    services_detected = Column(JSONB)
    
    # Scan metadata
    scan_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    scanner_device_id = Column(Integer, ForeignKey("network_devices.id"))
    scan_duration_ms = Column(Integer)

    # Relationships
    pool = relationship("IPPool")
    scanner_device = relationship("NetworkDevice", foreign_keys=[scanner_device_id])


# IPAM Configuration and Policies

class IPAMPolicy(Base):
    """IPAM policies and rules"""
    __tablename__ = "ipam_policies"

    id = Column(Integer, primary_key=True, index=True)
    
    # Policy definition
    name = Column(String(255), nullable=False)
    description = Column(Text)
    policy_type = Column(String(50))  # allocation, naming, retention, scanning
    
    # Policy scope
    pool_id = Column(Integer, ForeignKey("ip_pools.id"))  # Specific pool or global
    applies_to_children = Column(Boolean, default=True)
    
    # Policy rules (JSON configuration)
    rules = Column(JSONB, nullable=False)
    
    # Policy status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    pool = relationship("IPPool")


class IPAMTemplate(Base):
    """IP pool templates for standardized deployments"""
    __tablename__ = "ipam_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template definition
    name = Column(String(255), nullable=False)
    description = Column(Text)
    template_type = Column(String(50))  # site, customer, service
    
    # Template configuration
    ip_version = Column(Enum(IPVersion), nullable=False)
    prefix_length = Column(Integer, nullable=False)
    pool_type = Column(Enum(PoolType), nullable=False)
    
    # Default settings
    default_gateway_offset = Column(Integer, default=1)  # Gateway IP offset from network
    dns_servers = Column(ARRAY(String))
    domain_name = Column(String(255))
    lease_time = Column(Integer, default=86400)  # 24 hours
    
    # Allocation settings
    allocation_ranges = Column(JSONB)  # Predefined allocation ranges
    reserved_ranges = Column(JSONB)    # Reserved IP ranges
    
    # Template metadata
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# IPAM Reporting and Analytics

class IPAMUtilization(Base):
    """IP pool utilization snapshots for reporting"""
    __tablename__ = "ipam_utilization"

    id = Column(Integer, primary_key=True, index=True)
    
    # Utilization snapshot
    pool_id = Column(Integer, ForeignKey("ip_pools.id"), nullable=False)
    snapshot_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Utilization metrics
    total_addresses = Column(Integer, nullable=False)
    allocated_addresses = Column(Integer, nullable=False)
    reserved_addresses = Column(Integer, nullable=False)
    available_addresses = Column(Integer, nullable=False)
    utilization_percentage = Column(Integer, nullable=False)
    
    # Growth metrics
    allocations_last_24h = Column(Integer, default=0)
    releases_last_24h = Column(Integer, default=0)
    net_change_24h = Column(Integer, default=0)
    
    # Forecast data
    projected_exhaustion_date = Column(DateTime(timezone=True))
    growth_rate_per_day = Column(Integer, default=0)

    # Relationships
    pool = relationship("IPPool")
