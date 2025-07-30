"""
Internet Service Schemas

Pydantic schemas for Internet service management including:
- Service creation and updates
- Tariff plan configuration
- Provisioning requests
- Service status and monitoring
"""

from pydantic import BaseModel, Field, validator, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InternetServiceStatus(str, Enum):
    """Internet service status options."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    PROVISIONING = "provisioning"
    FAILED = "failed"


class InternetServiceSpeed(BaseModel):
    """Internet service speed configuration."""
    download_mbps: int = Field(..., ge=1, description="Download speed in Mbps")
    upload_mbps: int = Field(..., ge=1, description="Upload speed in Mbps")
    burst_download_mbps: Optional[int] = Field(None, ge=1, description="Burst download speed in Mbps")
    burst_upload_mbps: Optional[int] = Field(None, ge=1, description="Burst upload speed in Mbps")


class InternetServiceBase(BaseModel):
    """Base Internet service schema."""
    tariff_plan_id: int = Field(..., description="Tariff plan ID")
    speed_config: InternetServiceSpeed = Field(..., description="Speed configuration")
    data_limit_gb: Optional[int] = Field(None, ge=0, description="Monthly data limit in GB (null for unlimited)")
    static_ip_required: bool = Field(False, description="Whether static IP is required")
    installation_address: Optional[str] = Field(None, max_length=500, description="Installation address")
    notes: Optional[str] = Field(None, max_length=1000, description="Service notes")


class InternetServiceCreate(InternetServiceBase):
    """Schema for creating a new Internet service."""
    scheduled_activation: Optional[datetime] = Field(None, description="Scheduled activation date")
    
    @field_validator('scheduled_activation')
    @classmethod
    def validate_activation_date(cls, v):
        if v and v < datetime.now():
            raise ValueError('Scheduled activation cannot be in the past')
        return v


class InternetServiceUpdate(BaseModel):
    """Schema for updating an existing Internet service."""
    tariff_plan_id: Optional[int] = Field(None, description="Tariff plan ID")
    speed_config: Optional[InternetServiceSpeed] = Field(None, description="Speed configuration")
    data_limit_gb: Optional[int] = Field(None, ge=0, description="Monthly data limit in GB")
    static_ip_required: Optional[bool] = Field(None, description="Whether static IP is required")
    installation_address: Optional[str] = Field(None, max_length=500, description="Installation address")
    notes: Optional[str] = Field(None, max_length=1000, description="Service notes")
    status: Optional[InternetServiceStatus] = Field(None, description="Service status")


class InternetServiceProvisioningRequest(BaseModel):
    """Schema for Internet service provisioning requests."""
    router_id: Optional[int] = Field(None, description="Preferred router ID")
    ip_pool_id: Optional[int] = Field(None, description="Preferred IP pool ID")
    vlan_id: Optional[int] = Field(None, description="VLAN ID for service")
    priority: str = Field("normal", description="Provisioning priority: low, normal, high, urgent")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule provisioning for specific time")
    auto_activate: bool = Field(True, description="Automatically activate after successful provisioning")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError('Priority must be one of: low, normal, high, urgent')
        return v


class InternetService(InternetServiceBase):
    """Schema for Internet service response."""
    id: int
    customer_id: int
    status: InternetServiceStatus
    portal_username: Optional[str] = Field(None, description="Portal/PPPoE username")
    assigned_ip: Optional[str] = Field(None, description="Assigned IP address")
    router_id: Optional[int] = Field(None, description="Assigned router ID")
    activation_date: Optional[datetime] = Field(None, description="Service activation date")
    suspension_date: Optional[datetime] = Field(None, description="Service suspension date")
    termination_date: Optional[datetime] = Field(None, description="Service termination date")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    customer_name: Optional[str] = Field(None, description="Customer name")
    tariff_plan_name: Optional[str] = Field(None, description="Tariff plan name")
    monthly_fee: Optional[float] = Field(None, description="Monthly service fee")

    model_config = ConfigDict(from_attributes=True)

class InternetServiceSummary(BaseModel):
    """Simplified Internet service schema for lists."""
    id: int
    customer_id: int
    customer_name: str
    tariff_plan_name: str
    status: InternetServiceStatus
    speed_config: InternetServiceSpeed
    assigned_ip: Optional[str] = None
    monthly_fee: float
    activation_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class InternetServiceList(BaseModel):
    """Schema for paginated Internet service list response."""
    services: List[InternetServiceSummary]
    total: int = Field(..., description="Total number of services")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Items per page")
    pages: Optional[int] = Field(None, description="Total number of pages")


class InternetServiceUsage(BaseModel):
    """Schema for Internet service usage data."""
    service_id: int
    period_start: datetime
    period_end: datetime
    download_gb: float = Field(..., ge=0, description="Downloaded data in GB")
    upload_gb: float = Field(..., ge=0, description="Uploaded data in GB")
    total_gb: float = Field(..., ge=0, description="Total data usage in GB")
    peak_download_mbps: Optional[float] = Field(None, description="Peak download speed recorded")
    peak_upload_mbps: Optional[float] = Field(None, description="Peak upload speed recorded")
    session_count: int = Field(0, ge=0, description="Number of sessions")
    total_session_time: int = Field(0, ge=0, description="Total session time in seconds")

    model_config = ConfigDict(from_attributes=True)

class InternetServiceAnalytics(BaseModel):
    """Schema for Internet service analytics and reporting."""
    service_id: int
    customer_id: int
    current_month_usage: InternetServiceUsage
    previous_month_usage: Optional[InternetServiceUsage] = None
    usage_trend: str = Field(..., description="Usage trend: increasing, decreasing, stable")
    data_limit_utilization: Optional[float] = Field(None, description="Percentage of data limit used")
    average_speed_mbps: Optional[float] = Field(None, description="Average connection speed")
    uptime_percentage: float = Field(..., ge=0, le=100, description="Service uptime percentage")
    last_online: Optional[datetime] = Field(None, description="Last time service was online")

    model_config = ConfigDict(from_attributes=True)