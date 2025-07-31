"""
Network Device Integration Models

This module contains all network device-specific models including:
- MikroTik router integration and configuration
- Cisco device integration and management
- Device-specific configuration and monitoring
- Vendor-agnostic device abstractions
"""

from .cisco import CiscoAccessList, CiscoDevice, CiscoInterface, CiscoVLAN
from .device_management import (
    AlertSeverity,
    BackupStatus,
    DeviceAlert,
    DeviceConfigBackup,
    DeviceInterface,
    DeviceMonitoring,
    DeviceStatus,
    DeviceTemplate,
    DeviceType,
    ManagedDevice,
    MonitoringProtocol,
)
from .mikrotik import (
    MikroTikDevice,
    MikroTikDHCPLease,
    MikroTikFirewallRule,
    MikroTikHotspotUser,
    MikroTikInterface,
    MikroTikInterfaceStats,
    MikroTikPPPoESecret,
    MikroTikSimpleQueue,
    MikroTikSystemStats,
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
