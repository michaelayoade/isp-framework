"""
Network Device Integration Models

This module contains all network device-specific models including:
- MikroTik router integration and configuration
- Cisco device integration and management
- Device-specific configuration and monitoring
- Vendor-agnostic device abstractions
"""

from .device_management import (
    ManagedDevice,
    DeviceInterface,
    DeviceMonitoring,
    DeviceAlert,
    DeviceConfigBackup,
    DeviceTemplate,
    DeviceType, 
    DeviceStatus,
    AlertSeverity, 
    BackupStatus, 
    MonitoringProtocol
)
from .mikrotik import (
    MikroTikDevice, 
    MikroTikInterface, 
    MikroTikSimpleQueue, 
    MikroTikFirewallRule,
    MikroTikDHCPLease, 
    MikroTikPPPoESecret, 
    MikroTikHotspotUser,
    MikroTikSystemStats, 
    MikroTikInterfaceStats
)
from .cisco import (
    CiscoDevice, CiscoInterface, CiscoVLAN, CiscoAccessList
)

__all__ = [
    # Generic Device Management
    "ManagedDevice",
    "DeviceInterface",
    "DeviceMonitoring",
    "DeviceAlert",
    "DeviceConfigBackup",
    "DeviceTemplate",
    "DeviceType",
    "DeviceStatus",
    "AlertSeverity",
    "BackupStatus",
    "MonitoringProtocol",
    
    # MikroTik Integration
    "MikroTikDevice",
    "MikroTikInterface",
    "MikroTikSimpleQueue", 
    "MikroTikFirewallRule",
    "MikroTikDHCPLease",
    "MikroTikPPPoESecret",
    "MikroTikHotspotUser",
    "MikroTikSystemStats",
    "MikroTikInterfaceStats",
    
    # Cisco Integration
    "CiscoDevice",
    "CiscoInterface",
    "CiscoVLAN",
    "CiscoAccessList",
]
