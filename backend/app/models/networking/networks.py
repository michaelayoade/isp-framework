"""
Networks Module - Physical Infrastructure Management

This module provides vendor-agnostic network infrastructure management,
including sites, devices, connections, and physical topology.

Core Principles:
- Vendor independence: Core models work with any network vendor
- Separation of concerns: Physical topology separate from vendor-specific config
- Extensibility: Easy to add new device types and vendors
- Scalability: Supports complex multi-site enterprise networks
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import INET, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class DeviceType(enum.Enum):
    """Network device types - vendor agnostic"""
    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    CPE = "cpe"
    SERVER = "server"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    OPTICAL_EQUIPMENT = "optical"
    WIRELESS_BACKHAUL = "wireless_backhaul"
    MEDIA_CONVERTER = "media_converter"
    PATCH_PANEL = "patch_panel"


class SiteType(enum.Enum):
    """Network site types"""
    DATACENTER = "datacenter"
    POP = "pop"  # Point of Presence
    OFFICE = "office"
    TOWER = "tower"
    HEADEND = "headend"
    DISTRIBUTION = "distribution"
    ACCESS = "access"


class ConnectionType(enum.Enum):
    """Physical connection types"""
    FIBER = "fiber"
    ETHERNET = "ethernet"
    WIRELESS = "wireless"
    COAX = "coax"
    DSL = "dsl"
    SATELLITE = "satellite"


# Core Network Infrastructure Models

class NetworkSite(Base):
    """Physical network locations - vendor agnostic"""
    __tablename__ = "network_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    site_code = Column(String(50), unique=True)  # Unique site identifier
    site_type = Column(Enum(SiteType), nullable=False)
    
    # Location details
    address = Column(Text)
    latitude = Column(String(20))
    longitude = Column(String(20))
    elevation = Column(Integer)  # meters above sea level
    
    # Site characteristics
    description = Column(Text)
    contact_person = Column(String(255))
    contact_phone = Column(String(50))
    contact_email = Column(String(255))
    
    # Physical infrastructure
    power_backup = Column(Boolean, default=False)
    cooling_system = Column(Boolean, default=False)
    security_system = Column(Boolean, default=False)
    rack_count = Column(Integer, default=0)
    
    # Operational status
    is_active = Column(Boolean, default=True)
    maintenance_window = Column(String(100))  # e.g., "Sunday 02:00-06:00"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    devices = relationship("NetworkDevice", back_populates="site")
    cables = relationship("Cable", back_populates="site")


class NetworkDevice(Base):
    """All network devices - vendor agnostic core model"""
    __tablename__ = "network_devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), unique=True, nullable=False)
    device_type = Column(Enum(DeviceType), nullable=False)
    
    # Vendor information
    vendor = Column(String(100))  # mikrotik, cisco, ubiquiti, juniper, etc.
    model = Column(String(255))
    serial_number = Column(String(255), unique=True)
    firmware_version = Column(String(100))
    
    # Physical location
    site_id = Column(Integer, ForeignKey("network_sites.id"), nullable=False)
    rack_position = Column(String(50))  # e.g., "Rack-A-U12-U15"
    physical_location = Column(String(255))  # Additional location details
    
    # Network connectivity
    management_ip = Column(INET, unique=True)
    management_vlan = Column(Integer)
    
    # Device relationships
    parent_device_id = Column(Integer, ForeignKey("network_devices.id"))  # Hierarchical relationship
    primary_device_id = Column(Integer, ForeignKey("network_devices.id"))  # Backup/redundancy
    
    # Operational details
    description = Column(Text)
    purpose = Column(String(255))  # Brief description of device role
    criticality = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Status and monitoring
    operational_status = Column(String(20), default="unknown")  # up, down, degraded, maintenance
    administrative_status = Column(String(20), default="enabled")  # enabled, disabled, testing
    last_seen = Column(DateTime(timezone=True))
    uptime_seconds = Column(Integer, default=0)
    
    # Configuration management
    config_backup_enabled = Column(Boolean, default=True)
    last_config_backup = Column(DateTime(timezone=True))
    config_hash = Column(String(64))  # SHA-256 of current config
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    installed_date = Column(DateTime(timezone=True))
    warranty_expiry = Column(DateTime(timezone=True))

    # Relationships
    site = relationship("NetworkSite", back_populates="devices")
    parent_device = relationship("NetworkDevice", remote_side=[id], foreign_keys=[parent_device_id])
    child_devices = relationship("NetworkDevice", foreign_keys=[parent_device_id], overlaps="parent_device")
    primary_device = relationship("NetworkDevice", remote_side=[id], foreign_keys=[primary_device_id])
    backup_devices = relationship("NetworkDevice", foreign_keys=[primary_device_id], overlaps="primary_device")
    
    # Connection relationships
    outgoing_connections = relationship("DeviceConnection", foreign_keys="DeviceConnection.from_device_id", overlaps="from_device")
    incoming_connections = relationship("DeviceConnection", foreign_keys="DeviceConnection.to_device_id", overlaps="to_device")
    
    # Service relationships
    network_services = relationship("NetworkService", back_populates="device")
    device_metrics = relationship("DeviceMetric", back_populates="device")
    network_alerts = relationship("NetworkAlert", back_populates="device")
    
    # Configuration backups
    config_backups = relationship("DeviceConfiguration", back_populates="device")


class DeviceConnection(Base):
    """Physical connections between network devices"""
    __tablename__ = "device_connections"

    id = Column(Integer, primary_key=True, index=True)
    
    # Connection endpoints
    from_device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    to_device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    from_port = Column(String(50), nullable=False)
    to_port = Column(String(50), nullable=False)
    
    # Connection details
    connection_type = Column(Enum(ConnectionType), nullable=False)
    cable_id = Column(String(100), ForeignKey("cables.cable_id"))
    
    # Link characteristics
    bandwidth_mbps = Column(Integer)  # Link capacity in Mbps
    duplex = Column(String(10))  # full, half, auto
    mtu = Column(Integer, default=1500)
    
    # Operational status
    link_status = Column(String(20), default="unknown")  # up, down, degraded
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    from_device = relationship("NetworkDevice", foreign_keys=[from_device_id], overlaps="outgoing_connections")
    to_device = relationship("NetworkDevice", foreign_keys=[to_device_id], overlaps="incoming_connections")
    cable = relationship("Cable", back_populates="connections")


class Cable(Base):
    """Physical cable infrastructure"""
    __tablename__ = "cables"

    cable_id = Column(String(100), primary_key=True)  # Cable label/ID
    cable_type = Column(String(50), nullable=False)  # fiber, cat6, cat5e, coax
    
    # Physical characteristics
    length_meters = Column(Integer)
    fiber_count = Column(Integer)  # For fiber cables
    conductor_count = Column(Integer)  # For copper cables
    
    # Installation details
    site_id = Column(Integer, ForeignKey("network_sites.id"))
    installation_date = Column(DateTime(timezone=True))
    route_description = Column(Text)  # Physical path description
    
    # Cable endpoints
    endpoint_a = Column(String(255))  # Physical location description
    endpoint_b = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    condition = Column(String(20), default="good")  # good, fair, poor, damaged
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    site = relationship("NetworkSite", back_populates="cables")
    connections = relationship("DeviceConnection", back_populates="cable")


# Network Services and Configuration

class NetworkService(Base):
    """Services running on network devices"""
    __tablename__ = "network_services"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    
    # Service details
    service_type = Column(String(50), nullable=False)  # dhcp, dns, ntp, radius, snmp
    service_name = Column(String(255))
    service_config = Column(JSONB)  # Vendor-agnostic configuration
    
    # Service status
    is_active = Column(Boolean, default=True)
    is_monitored = Column(Boolean, default=True)
    port = Column(Integer)
    protocol = Column(String(10))  # tcp, udp, both
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("NetworkDevice", back_populates="network_services")


class DeviceConfiguration(Base):
    """Device configuration backup and versioning"""
    __tablename__ = "device_configurations"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    
    # Configuration data
    config_data = Column(Text, nullable=False)
    config_hash = Column(String(64), nullable=False)  # SHA-256
    config_format = Column(String(50))  # text, json, xml, binary
    
    # Version information
    version_number = Column(Integer)
    is_current = Column(Boolean, default=False)
    is_startup = Column(Boolean, default=False)  # Startup vs running config
    
    # Backup metadata
    backup_method = Column(String(50))  # manual, scheduled, triggered
    backup_size_bytes = Column(Integer)
    compression_used = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    backup_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device = relationship("NetworkDevice", back_populates="config_backups")


# Network Monitoring and Alerting

class DeviceMetric(Base):
    """Device performance metrics and monitoring data"""
    __tablename__ = "device_metrics"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    
    # Metric details
    metric_type = Column(String(50), nullable=False)  # cpu, memory, interface_traffic, temperature
    metric_name = Column(String(100))  # Specific metric name
    metric_value = Column(String(255))  # Flexible value storage
    metric_unit = Column(String(20))  # %, bytes, celsius, etc.
    
    # Interface-specific metrics
    interface_name = Column(String(50))  # For interface-specific metrics
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    device = relationship("NetworkDevice", back_populates="device_metrics")


class NetworkAlert(Base):
    """Network alerts and incidents"""
    __tablename__ = "network_alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"))
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # device_down, high_cpu, interface_down
    severity = Column(String(20), nullable=False)    # critical, warning, info
    title = Column(String(255), nullable=False)
    message = Column(Text)
    
    # Alert context
    metric_type = Column(String(50))  # Related metric type
    threshold_value = Column(String(100))  # Threshold that was breached
    current_value = Column(String(100))   # Current value when alert triggered
    
    # Alert lifecycle
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("administrators.id"))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    last_occurrence = Column(DateTime(timezone=True))
    occurrence_count = Column(Integer, default=1)

    # Relationships
    device = relationship("NetworkDevice", back_populates="network_alerts")


# Network Change Management

class NetworkChange(Base):
    """Track network changes for audit and rollback"""
    __tablename__ = "network_changes"

    change_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("network_devices.id"))
    
    # Change details
    change_type = Column(String(50), nullable=False)  # config, physical, ip_assignment, firmware
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Change management
    change_category = Column(String(50))  # emergency, standard, normal
    risk_level = Column(String(20))  # low, medium, high
    rollback_plan = Column(Text)
    
    # Implementation details
    implemented_by = Column(Integer, ForeignKey("administrators.id"))
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    
    # Scheduling
    scheduled_time = Column(DateTime(timezone=True))
    maintenance_window_start = Column(DateTime(timezone=True))
    maintenance_window_end = Column(DateTime(timezone=True))
    
    # Execution
    started_time = Column(DateTime(timezone=True))
    completed_time = Column(DateTime(timezone=True))
    status = Column(String(20), default="planned")  # planned, in_progress, completed, failed, rolled_back
    
    # Results
    success = Column(Boolean)
    error_message = Column(Text)
    rollback_performed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    device = relationship("NetworkDevice")


# Network Redundancy and High Availability

class NetworkRedundancy(Base):
    """Network redundancy and failover configuration"""
    __tablename__ = "network_redundancy"

    id = Column(Integer, primary_key=True, index=True)
    
    # Redundancy relationship
    primary_device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    backup_device_id = Column(Integer, ForeignKey("network_devices.id"), nullable=False)
    
    # Redundancy configuration
    redundancy_type = Column(String(50), nullable=False)  # active_passive, active_active, load_balance
    failover_type = Column(String(50))  # manual, automatic, hybrid
    priority = Column(Integer, default=1)
    
    # Failover settings
    health_check_interval = Column(Integer, default=30)  # seconds
    failover_threshold = Column(Integer, default=3)  # failed checks before failover
    failback_enabled = Column(Boolean, default=True)
    failback_delay = Column(Integer, default=300)  # seconds
    
    # Status
    is_active = Column(Boolean, default=True)
    current_active_device = Column(String(20))  # primary, backup, both
    last_failover = Column(DateTime(timezone=True))
    failover_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    primary_device = relationship("NetworkDevice", foreign_keys=[primary_device_id])
    backup_device = relationship("NetworkDevice", foreign_keys=[backup_device_id])
