"""
Generic Network Device Management Module

This module provides vendor-agnostic device management functionality for all network infrastructure:
- Routers, switches, access points, firewalls, load balancers
- SNMP-based monitoring and management
- Configuration backup and restore
- Health monitoring and alerting
- Performance trending and capacity planning
- Firmware management and updates

Core Principles:
- Vendor agnostic: Works with any SNMP-capable device
- Extensible: Easy to add new device types and monitoring metrics
- Scalable: Supports large-scale network infrastructure
- Reliable: Built-in error handling and retry mechanisms
"""

import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Float, Index
from sqlalchemy.dialects.postgresql import INET, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DeviceType(enum.Enum):
    """Network device types"""
    ROUTER = "router"
    SWITCH = "switch"
    ACCESS_POINT = "access_point"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    GATEWAY = "gateway"
    BRIDGE = "bridge"
    REPEATER = "repeater"
    MODEM = "modem"
    OTHER = "other"


class DeviceStatus(enum.Enum):
    """Device operational status"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class MonitoringProtocol(enum.Enum):
    """Device monitoring protocols"""
    SNMP_V1 = "snmp_v1"
    SNMP_V2C = "snmp_v2c"
    SNMP_V3 = "snmp_v3"
    ICMP = "icmp"
    SSH = "ssh"
    TELNET = "telnet"
    HTTP = "http"
    HTTPS = "https"
    API = "api"


class AlertSeverity(enum.Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class BackupStatus(enum.Enum):
    """Configuration backup status"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    SCHEDULED = "scheduled"


# Core Device Management Models

class ManagedDevice(Base):
    """
    Generic managed device model for device management and monitoring.
    Supports all types of network infrastructure devices.
    """
    __tablename__ = "managed_devices"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Device Information
    hostname = Column(String(255), nullable=False, index=True)
    device_type = Column(Enum(DeviceType), nullable=False)
    vendor = Column(String(100))  # cisco, mikrotik, ubiquiti, juniper, etc.
    model = Column(String(100))
    serial_number = Column(String(100), unique=True)
    
    # Network Configuration
    management_ip = Column(INET, nullable=False, unique=True, index=True)
    secondary_ips = Column(ARRAY(String))  # Additional management IPs
    mac_address = Column(String(17))
    location_id = Column(Integer, ForeignKey("locations.id"))
    
    # Physical Information
    rack_location = Column(String(100))
    rack_unit = Column(String(20))
    physical_location = Column(String(255))
    asset_tag = Column(String(100))
    
    # Management Access
    snmp_enabled = Column(Boolean, default=True)
    snmp_version = Column(String(10), default="v2c")  # v1, v2c, v3
    snmp_community_ro = Column(String(100), default="public")
    snmp_community_rw = Column(String(100))
    snmp_port = Column(Integer, default=161)
    
    # SSH/Telnet Access
    ssh_enabled = Column(Boolean, default=True)
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String(100))
    ssh_password = Column(String(255))  # Encrypted
    telnet_enabled = Column(Boolean, default=False)
    telnet_port = Column(Integer, default=23)
    
    # Web Management
    web_management_enabled = Column(Boolean, default=False)
    web_management_port = Column(Integer, default=80)
    web_management_ssl = Column(Boolean, default=False)
    web_management_ssl_port = Column(Integer, default=443)
    
    # Device Status
    status = Column(Enum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    last_seen = Column(DateTime(timezone=True))
    uptime = Column(Integer)  # seconds
    
    # Hardware Information
    cpu_count = Column(Integer)
    total_memory = Column(Integer)  # MB
    total_storage = Column(Integer)  # MB
    power_consumption = Column(Float)  # watts
    
    # Software Information
    os_version = Column(String(100))
    firmware_version = Column(String(100))
    boot_version = Column(String(100))
    
    # Monitoring Configuration
    monitoring_enabled = Column(Boolean, default=True)
    monitoring_interval = Column(Integer, default=300)  # seconds
    monitoring_protocols = Column(ARRAY(String))  # snmp, icmp, ssh, etc.
    
    # Management Settings
    auto_discovery = Column(Boolean, default=True)
    config_backup_enabled = Column(Boolean, default=True)
    config_backup_schedule = Column(String(100))  # cron expression
    
    # Custom Fields
    tags = Column(ARRAY(String))  # Custom tags for grouping
    custom_fields = Column(JSONB, default=dict)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    discovered_at = Column(DateTime(timezone=True))
    
    # Relationships
    location = relationship("Location", back_populates="network_devices")
    monitoring_data = relationship("DeviceMonitoring", back_populates="device", cascade="all, delete-orphan")
    config_backups = relationship("DeviceConfigBackup", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("DeviceAlert", back_populates="device", cascade="all, delete-orphan")
    interfaces = relationship("DeviceInterface", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ManagedDevice(id={self.id}, hostname='{self.hostname}', type='{self.device_type}', ip='{self.management_ip}')>"


class DeviceInterface(Base):
    """Network device interfaces"""
    __tablename__ = "device_interfaces"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("managed_devices.id"), nullable=False, index=True)
    
    # Interface Information
    interface_name = Column(String(100), nullable=False)
    interface_index = Column(Integer)  # SNMP ifIndex
    interface_type = Column(String(50))  # ethernet, serial, loopback, etc.
    interface_description = Column(String(255))
    
    # Physical Properties
    mac_address = Column(String(17))
    mtu = Column(Integer, default=1500)
    speed = Column(Integer)  # bps
    duplex = Column(String(10))  # full, half, auto
    
    # IP Configuration
    ip_addresses = Column(ARRAY(String))
    subnet_masks = Column(ARRAY(String))
    
    # Status
    admin_status = Column(String(20), default="up")  # up, down, testing
    oper_status = Column(String(20), default="down")  # up, down, testing, unknown
    
    # VLAN Configuration
    vlan_id = Column(Integer)
    vlan_mode = Column(String(20))  # access, trunk, hybrid
    allowed_vlans = Column(String(255))
    
    # Statistics (latest values)
    in_octets = Column(Integer, default=0)
    out_octets = Column(Integer, default=0)
    in_packets = Column(Integer, default=0)
    out_packets = Column(Integer, default=0)
    in_errors = Column(Integer, default=0)
    out_errors = Column(Integer, default=0)
    in_discards = Column(Integer, default=0)
    out_discards = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_stats_update = Column(DateTime(timezone=True))
    
    # Relationships
    device = relationship("ManagedDevice", back_populates="interfaces")
    
    def __repr__(self):
        return f"<DeviceInterface(id={self.id}, device_id={self.device_id}, name='{self.interface_name}')>"


class DeviceMonitoring(Base):
    """Device monitoring metrics and performance data"""
    __tablename__ = "device_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("managed_devices.id"), nullable=False, index=True)
    
    # Metric Information
    metric_name = Column(String(100), nullable=False)  # cpu_usage, memory_usage, etc.
    metric_category = Column(String(50))  # system, interface, custom
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # percent, bytes, bps, etc.
    
    # Context Information
    interface_name = Column(String(100))  # For interface-specific metrics
    additional_context = Column(JSONB, default=dict)  # Extra metric context
    
    # Monitoring Details
    collection_method = Column(String(20))  # snmp, api, ssh, ping
    response_time = Column(Float)  # Collection response time in ms
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    device = relationship("ManagedDevice", back_populates="monitoring_data")
    
    def __repr__(self):
        return f"<DeviceMonitoring(device_id={self.device_id}, metric='{self.metric_name}', value={self.metric_value})>"


class DeviceAlert(Base):
    """Device alerts and notifications"""
    __tablename__ = "device_alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("managed_devices.id"), nullable=False, index=True)
    
    # Alert Information
    alert_type = Column(String(100), nullable=False)  # cpu_high, interface_down, device_unreachable
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Threshold Information
    metric_name = Column(String(100))
    threshold_value = Column(Float)
    current_value = Column(Float)
    threshold_operator = Column(String(10))  # >, <, >=, <=, ==, !=
    
    # Alert Status
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    
    # Resolution
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_methods = Column(ARRAY(String))  # email, sms, webhook
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("ManagedDevice", back_populates="alerts")
    
    def __repr__(self):
        return f"<DeviceAlert(id={self.id}, device_id={self.device_id}, type='{self.alert_type}', severity='{self.severity}')>"


class DeviceConfigBackup(Base):
    """Device configuration backups"""
    __tablename__ = "device_config_backups"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("managed_devices.id"), nullable=False, index=True)
    
    # Backup Information
    backup_type = Column(String(50), default="full")  # full, running, startup, partial
    backup_method = Column(String(20))  # snmp, ssh, tftp, scp, api
    backup_status = Column(Enum(BackupStatus), default=BackupStatus.SCHEDULED)
    
    # File Information
    filename = Column(String(255))
    file_size = Column(Integer)  # bytes
    file_path = Column(String(500))  # Storage path
    checksum = Column(String(64))  # MD5 or SHA256
    compression = Column(String(20))  # gzip, bzip2, none
    
    # Configuration Content
    config_content = Column(Text)  # For small configs, store directly
    config_diff = Column(Text)  # Diff from previous backup
    
    # Backup Metadata
    config_version = Column(String(100))
    device_os_version = Column(String(100))
    backup_trigger = Column(String(50))  # scheduled, manual, pre_change, post_change
    
    # Status Information
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    scheduled_at = Column(DateTime(timezone=True))
    
    # Relationships
    device = relationship("ManagedDevice", back_populates="config_backups")
    
    def __repr__(self):
        return f"<DeviceConfigBackup(id={self.id}, device_id={self.device_id}, status='{self.backup_status}')>"


class DeviceTemplate(Base):
    """Device configuration and monitoring templates"""
    __tablename__ = "device_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template Information
    template_name = Column(String(100), nullable=False, unique=True)
    template_description = Column(Text)
    device_type = Column(Enum(DeviceType))
    vendor = Column(String(100))
    model_pattern = Column(String(100))  # Regex pattern for model matching
    
    # Monitoring Configuration
    monitoring_profile = Column(JSONB, default=dict)  # Metrics to collect
    alert_thresholds = Column(JSONB, default=dict)  # Alert threshold definitions
    backup_schedule = Column(String(100))  # Cron expression
    
    # SNMP Configuration
    snmp_oids = Column(JSONB, default=dict)  # Custom OIDs to monitor
    snmp_community_default = Column(String(100))
    
    # Configuration Templates
    config_templates = Column(JSONB, default=dict)  # Jinja2 templates for config generation
    provisioning_scripts = Column(JSONB, default=dict)  # Automation scripts
    
    # Template Status
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DeviceTemplate(id={self.id}, name='{self.template_name}', type='{self.device_type}')>"


# Database Indexes for Performance
Index('idx_managed_devices_ip', ManagedDevice.management_ip)
Index('idx_managed_devices_hostname', ManagedDevice.hostname)
Index('idx_managed_devices_type_status', ManagedDevice.device_type, ManagedDevice.status)
Index('idx_device_monitoring_device_metric', DeviceMonitoring.device_id, DeviceMonitoring.metric_name)
Index('idx_device_monitoring_timestamp', DeviceMonitoring.timestamp.desc())
Index('idx_device_alerts_active', DeviceAlert.device_id, DeviceAlert.is_active)
Index('idx_device_interfaces_device', DeviceInterface.device_id)
Index('idx_device_config_backups_device_status', DeviceConfigBackup.device_id, DeviceConfigBackup.backup_status)
