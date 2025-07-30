"""Pydantic schemas for device management and MAC authentication."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import re


class DeviceBase(BaseModel):
    """Base device schema with common fields."""
    mac_address: str = Field(..., description="MAC address in AA:BB:CC:DD:EE:FF format")
    name: Optional[str] = Field(None, max_length=255, description="Device name")
    description: Optional[str] = Field(None, description="Device description")
    device_type: Optional[str] = Field(None, max_length=50, description="Device type (router, switch, camera, etc.)")
    
    @validator('mac_address')
    def validate_mac_address(cls, v):
        """Validate and normalize MAC address format."""
        if not v:
            raise ValueError("MAC address is required")
        
        # Remove common separators and convert to uppercase
        cleaned = v.replace(":", "").replace("-", "").replace(".", "").upper()
        
        # Validate length
        if len(cleaned) != 12:
            raise ValueError("MAC address must be 12 hex characters")
        
        # Validate hex characters
        if not re.match(r'^[0-9A-F]{12}$', cleaned):
            raise ValueError("MAC address must contain only hex characters")
        
        # Format as AA:BB:CC:DD:EE:FF
        return ":".join([cleaned[i:i+2] for i in range(0, 12, 2)])


class DeviceCreate(DeviceBase):
    """Schema for creating a new device."""
    customer_id: int = Field(..., description="Customer ID who owns the device")


class DeviceUpdate(BaseModel):
    """Schema for updating device information."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    device_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, regex="^(pending|active|blocked|expired)$")


class DeviceApproval(BaseModel):
    """Schema for approving/rejecting devices."""
    is_approved: bool = Field(..., description="Whether to approve the device")
    approval_reason: Optional[str] = Field(None, description="Reason for approval/rejection")


class DeviceResponse(DeviceBase):
    """Schema for device API responses."""
    id: int
    customer_id: int
    status: str
    is_auto_registered: bool
    is_approved: bool
    last_ip_address: Optional[str] = None
    last_nas_identifier: Optional[str] = None
    last_nas_port: Optional[str] = None
    first_seen: datetime
    last_seen: datetime
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Schema for paginated device list responses."""
    devices: List[DeviceResponse]
    total: int
    page: int
    per_page: int
    pages: int


class DeviceStats(BaseModel):
    """Schema for device statistics."""
    total_devices: int
    active_devices: int
    pending_devices: int
    blocked_devices: int
    auto_registered_devices: int
    devices_last_24h: int
    devices_last_7d: int


# Device Group Schemas
class DeviceGroupBase(BaseModel):
    """Base device group schema."""
    name: str = Field(..., max_length=255, description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    auto_approve_devices: bool = Field(False, description="Auto-approve new devices in this group")
    default_device_status: str = Field("pending", regex="^(pending|active|blocked)$")
    bandwidth_limit_mbps: Optional[int] = Field(None, ge=1, description="Bandwidth limit in Mbps")


class DeviceGroupCreate(DeviceGroupBase):
    """Schema for creating device groups."""
    customer_id: int = Field(..., description="Customer ID who owns the group")


class DeviceGroupUpdate(BaseModel):
    """Schema for updating device groups."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    auto_approve_devices: Optional[bool] = None
    default_device_status: Optional[str] = Field(None, regex="^(pending|active|blocked)$")
    bandwidth_limit_mbps: Optional[int] = Field(None, ge=1)


class DeviceGroupResponse(DeviceGroupBase):
    """Schema for device group API responses."""
    id: int
    customer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    device_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class DeviceGroupMemberResponse(BaseModel):
    """Schema for device group membership."""
    device_id: int
    group_id: int
    added_at: datetime
    device: Optional[DeviceResponse] = None
    
    class Config:
        from_attributes = True


# MAC Authentication Service Schemas
class ServiceMacAuthSettings(BaseModel):
    """Schema for service MAC authentication settings."""
    mac_auth_enabled: bool = Field(False, description="Enable MAC-based authentication")
    auto_register_mac: bool = Field(False, description="Auto-register unknown MAC addresses")
    max_devices: int = Field(5, ge=1, le=100, description="Maximum devices allowed")


class ServiceMacAuthUpdate(BaseModel):
    """Schema for updating service MAC auth settings."""
    mac_auth_enabled: Optional[bool] = None
    auto_register_mac: Optional[bool] = None
    max_devices: Optional[int] = Field(None, ge=1, le=100)


# RADIUS Integration Schemas
class RadiusDeviceRequest(BaseModel):
    """Schema for RADIUS device authentication requests."""
    mac_address: str = Field(..., description="MAC address from RADIUS request")
    nas_identifier: Optional[str] = Field(None, description="NAS identifier")
    nas_port: Optional[str] = Field(None, description="NAS port")
    client_ip: Optional[str] = Field(None, description="Client IP address")
    service_id: Optional[int] = Field(None, description="Service ID for authentication")


class RadiusDeviceResponse(BaseModel):
    """Schema for RADIUS device authentication responses."""
    access_granted: bool = Field(..., description="Whether access is granted")
    device_id: Optional[int] = Field(None, description="Device ID if found")
    customer_id: Optional[int] = Field(None, description="Customer ID")
    service_id: Optional[int] = Field(None, description="Service ID")
    bandwidth_limit_down: Optional[int] = Field(None, description="Download bandwidth limit in kbps")
    bandwidth_limit_up: Optional[int] = Field(None, description="Upload bandwidth limit in kbps")
    session_timeout: Optional[int] = Field(None, description="Session timeout in seconds")
    vlan_id: Optional[int] = Field(None, description="VLAN ID for the session")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if access denied")


# Bulk Operations Schemas
class DeviceBulkApproval(BaseModel):
    """Schema for bulk device approval operations."""
    device_ids: List[int] = Field(..., description="List of device IDs to approve")
    is_approved: bool = Field(..., description="Whether to approve or reject")
    approval_reason: Optional[str] = Field(None, description="Reason for bulk approval/rejection")


class DeviceBulkUpdate(BaseModel):
    """Schema for bulk device updates."""
    device_ids: List[int] = Field(..., description="List of device IDs to update")
    status: Optional[str] = Field(None, regex="^(pending|active|blocked|expired)$")
    device_type: Optional[str] = Field(None, max_length=50)


class DeviceBulkResponse(BaseModel):
    """Schema for bulk operation responses."""
    success_count: int = Field(..., description="Number of successful operations")
    failed_count: int = Field(..., description="Number of failed operations")
    errors: List[str] = Field(default_factory=list, description="List of error messages")


# Search and Filter Schemas
class DeviceFilters(BaseModel):
    """Schema for device search and filtering."""
    customer_id: Optional[int] = None
    status: Optional[str] = Field(None, regex="^(pending|active|blocked|expired)$")
    device_type: Optional[str] = None
    is_approved: Optional[bool] = None
    is_auto_registered: Optional[bool] = None
    mac_address: Optional[str] = None
    name: Optional[str] = None
    last_seen_after: Optional[datetime] = None
    last_seen_before: Optional[datetime] = None
    nas_identifier: Optional[str] = None


class DeviceSort(BaseModel):
    """Schema for device sorting options."""
    field: str = Field("last_seen", regex="^(name|mac_address|status|last_seen|created_at)$")
    direction: str = Field("desc", regex="^(asc|desc)$")
