from ._base import BaseSchema
"""
Pydantic Schemas for Modular Network Architecture

This module defines the request/response schemas for the new modular network
architecture API endpoints, providing type safety and validation for all
network-related operations.
"""

from pydantic import  Field, field_validator
from typing import List, Optional, Dict, Any, Union, Generic, TypeVar
from datetime import datetime
from enum import Enum
import ipaddress

# Generic type for paginated responses
T = TypeVar('T')


# Enums for validation
class DeviceTypeEnum(str, Enum):
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


class SiteTypeEnum(str, Enum):
    DATACENTER = "datacenter"
    POP = "pop"
    OFFICE = "office"
    TOWER = "tower"
    HEADEND = "headend"
    DISTRIBUTION = "distribution"
    ACCESS = "access"


class ConnectionTypeEnum(str, Enum):
    FIBER = "fiber"
    ETHERNET = "ethernet"
    WIRELESS = "wireless"
    COAX = "coax"
    DSL = "dsl"
    SATELLITE = "satellite"


class PoolTypeEnum(str, Enum):
    CUSTOMER = "customer"
    INFRASTRUCTURE = "infrastructure"
    MANAGEMENT = "management"
    TRANSIT = "transit"


class AllocationStatusEnum(str, Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    EXPIRED = "expired"


class AllocationTypeEnum(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    RESERVED = "reserved"


# Network Site Schemas
class NetworkSiteBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    site_code: Optional[str] = Field(None, max_length=50)
    site_type: SiteTypeEnum
    address: Optional[str] = None
    latitude: Optional[str] = Field(None, max_length=20)
    longitude: Optional[str] = Field(None, max_length=20)
    elevation: Optional[int] = None
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    power_backup: bool = False
    cooling_system: bool = False
    security_system: bool = False
    rack_count: int = Field(0, ge=0)
    is_active: bool = True
    maintenance_window: Optional[str] = Field(None, max_length=100)


class NetworkSiteCreate(NetworkSiteBase):
    pass


class NetworkSiteUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    site_type: Optional[SiteTypeEnum] = None
    address: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    elevation: Optional[int] = None
    description: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    power_backup: Optional[bool] = None
    cooling_system: Optional[bool] = None
    security_system: Optional[bool] = None
    rack_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    maintenance_window: Optional[str] = None


class NetworkSiteResponse(NetworkSiteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# Network Device Schemas
class NetworkDeviceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    device_type: DeviceTypeEnum
    site_id: Optional[int] = None
    vendor: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=255)
    firmware_version: Optional[str] = Field(None, max_length=100)
    management_ip: Optional[str] = None
    rack_position: Optional[str] = Field(None, max_length=50)
    power_consumption: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: bool = True
    is_monitored: bool = True

    @field_validator('management_ip')
    def validate_management_ip(cls, v):
        if v:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v


class NetworkDeviceCreate(NetworkDeviceBase):
    pass


class NetworkDeviceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_type: Optional[DeviceTypeEnum] = None
    site_id: Optional[int] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    management_ip: Optional[str] = None
    rack_position: Optional[str] = None
    power_consumption: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_monitored: Optional[bool] = None


class NetworkDeviceResponse(NetworkDeviceBase):
    id: int
    last_seen: Optional[datetime] = None
    uptime_seconds: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None


# Vendor Configuration Schemas
class VendorConfigurationCreate(BaseSchema):
    vendor: str = Field(..., min_length=1)
    configuration: Dict[str, Any]


# IP Pool Schemas
class IPPoolBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    network: str
    prefix_length: int = Field(..., ge=1, le=128)
    pool_type: PoolTypeEnum
    description: Optional[str] = None
    location_id: Optional[int] = None
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    gateway: Optional[str] = None
    dns_servers: Optional[List[str]] = None
    is_active: bool = True
    allow_auto_assignment: bool = True

    @field_validator('network')
    def validate_network(cls, v):
        try:
            ipaddress.ip_network(v, strict=False)
        except ValueError:
            raise ValueError('Invalid network format')
        return v

    @field_validator('gateway')
    def validate_gateway(cls, v):
        if v:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid gateway IP address')
        return v

    @field_validator('dns_servers')
    def validate_dns_servers(cls, v):
        if v:
            for dns in v:
                try:
                    ipaddress.ip_address(dns)
                except ValueError:
                    raise ValueError(f'Invalid DNS server IP address: {dns}')
        return v


class IPPoolCreate(IPPoolBase):
    pass


class IPPoolUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    gateway: Optional[str] = None
    dns_servers: Optional[List[str]] = None
    is_active: Optional[bool] = None
    allow_auto_assignment: Optional[bool] = None


class IPPoolResponse(IPPoolBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# IP Allocation Schemas
class IPAllocationBase(BaseSchema):
    ip_address: str
    allocation_type: AllocationTypeEnum
    customer_id: Optional[int] = None
    device_id: Optional[int] = None
    service_id: Optional[int] = None
    hostname: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator('ip_address')
    def validate_ip_address(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v


class IPAllocationCreate(IPAllocationBase):
    pass


class IPAllocationResponse(IPAllocationBase):
    id: int
    pool_id: int
    status: AllocationStatusEnum
    allocated_at: datetime
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# IP Utilization Schema
class IPUtilizationResponse(BaseSchema):
    pool: IPPoolResponse
    total_addresses: int
    allocations: Dict[str, int]
    utilization_percentage: float


# Network Topology Schemas
class TopologyNode(BaseSchema):
    id: int
    name: str
    type: str
    vendor: Optional[str] = None
    site_id: Optional[int] = None
    is_active: bool


class TopologyEdge(BaseSchema):
    from_: int = Field(..., alias="from")
    to: int
    type: str
    bandwidth: Optional[int] = None
    status: str


class NetworkTopologyResponse(BaseSchema):
    nodes: List[TopologyNode]
    edges: List[TopologyEdge]


class DeviceConnectionCreate(BaseSchema):
    from_device_id: int
    to_device_id: int
    from_port: str = Field(..., max_length=50)
    to_port: str = Field(..., max_length=50)
    connection_type: ConnectionTypeEnum
    cable_id: Optional[str] = None
    bandwidth_mbps: Optional[int] = Field(None, gt=0)
    duplex: Optional[str] = Field(None, max_length=10)
    mtu: int = Field(1500, ge=64, le=9216)
    description: Optional[str] = None


# Monitoring Schemas
class DeviceMetricCreate(BaseSchema):
    device_id: int
    metric_type: str = Field(..., max_length=50)
    metric_name: Optional[str] = Field(None, max_length=100)
    metric_value: str = Field(..., max_length=255)
    metric_unit: Optional[str] = Field(None, max_length=20)
    interface_name: Optional[str] = Field(None, max_length=50)


class NetworkAlertResponse(BaseSchema):
    id: int
    device_id: Optional[int] = None
    alert_type: str
    severity: str
    title: str
    message: Optional[str] = None
    metric_type: Optional[str] = None
    threshold_value: Optional[str] = None
    current_value: Optional[str] = None
    is_active: bool
    is_acknowledged: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    occurrence_count: int


# Pagination Schema
class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int
    has_next: bool = False
    has_previous: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        self.has_next = (self.skip + self.limit) < self.total
        self.has_previous = self.skip > 0


# Filter Parameters Schema
class FilterParams(BaseSchema):
    search: Optional[str] = None
    site_id: Optional[int] = None
    device_type: Optional[DeviceTypeEnum] = None
    vendor: Optional[str] = None
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


# Migration Status Schema
class MigrationStatusResponse(BaseSchema):
    phase: int
    status: str
    message: str
    progress_percentage: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    errors: List[str] = []


# Network Statistics Schema
class NetworkStatistics(BaseSchema):
    sites: Dict[str, Any]
    devices: Dict[str, Any]
    ip_pools: Dict[str, Any]
    monitoring: Dict[str, Any]
    timestamp: datetime
