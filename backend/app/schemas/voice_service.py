"""
Voice Service Schemas

Pydantic schemas for Voice service management including:
- Service creation and updates
- Call plan configuration
- Phone number assignment
- Service status and monitoring
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VoiceServiceStatus(str, Enum):
    """Voice service status options."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    PROVISIONING = "provisioning"
    FAILED = "failed"


class CallPlanType(str, Enum):
    """Call plan types."""
    UNLIMITED_LOCAL = "unlimited_local"
    UNLIMITED_NATIONAL = "unlimited_national"
    UNLIMITED_INTERNATIONAL = "unlimited_international"
    METERED = "metered"
    PREPAID = "prepaid"


class VoiceServiceBase(BaseModel):
    """Base Voice service schema."""
    call_plan_id: int = Field(..., description="Call plan ID")
    phone_number: Optional[str] = Field(None, max_length=20, description="Assigned phone number")
    call_plan_type: CallPlanType = Field(..., description="Type of call plan")
    monthly_minutes: Optional[int] = Field(None, ge=0, description="Monthly minute allowance (null for unlimited)")
    international_calling: bool = Field(False, description="International calling enabled")
    voicemail_enabled: bool = Field(True, description="Voicemail service enabled")
    call_forwarding_enabled: bool = Field(False, description="Call forwarding enabled")
    caller_id_enabled: bool = Field(True, description="Caller ID service enabled")
    notes: Optional[str] = Field(None, max_length=1000, description="Service notes")


class VoiceServiceCreate(VoiceServiceBase):
    """Schema for creating a new Voice service."""
    preferred_area_code: Optional[str] = Field(None, max_length=10, description="Preferred area code for number assignment")
    scheduled_activation: Optional[datetime] = Field(None, description="Scheduled activation date")
    
    @field_validator('scheduled_activation')
    @classmethod
    def validate_activation_date(cls, v):
        if v and v < datetime.now():
            raise ValueError('Scheduled activation cannot be in the past')
        return v


class VoiceServiceUpdate(BaseModel):
    """Schema for updating an existing Voice service."""
    call_plan_id: Optional[int] = Field(None, description="Call plan ID")
    call_plan_type: Optional[CallPlanType] = Field(None, description="Type of call plan")
    monthly_minutes: Optional[int] = Field(None, ge=0, description="Monthly minute allowance")
    international_calling: Optional[bool] = Field(None, description="International calling enabled")
    voicemail_enabled: Optional[bool] = Field(None, description="Voicemail service enabled")
    call_forwarding_enabled: Optional[bool] = Field(None, description="Call forwarding enabled")
    caller_id_enabled: Optional[bool] = Field(None, description="Caller ID service enabled")
    notes: Optional[str] = Field(None, max_length=1000, description="Service notes")
    status: Optional[VoiceServiceStatus] = Field(None, description="Service status")


class VoiceServiceProvisioningRequest(BaseModel):
    """Schema for Voice service provisioning requests."""
    sip_server_id: Optional[int] = Field(None, description="Preferred SIP server ID")
    trunk_group_id: Optional[int] = Field(None, description="Trunk group ID")
    priority: str = Field("normal", description="Provisioning priority: low, normal, high, urgent")
    scheduled_for: Optional[datetime] = Field(None, description="Schedule provisioning for specific time")
    auto_activate: bool = Field(True, description="Automatically activate after successful provisioning")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError('Priority must be one of: low, normal, high, urgent')
        return v


class VoiceService(VoiceServiceBase):
    """Schema for Voice service response."""
    id: int
    customer_id: int
    status: VoiceServiceStatus
    sip_username: Optional[str] = Field(None, description="SIP username for authentication")
    sip_password: Optional[str] = Field(None, description="SIP password")
    sip_server: Optional[str] = Field(None, description="Assigned SIP server")
    activation_date: Optional[datetime] = Field(None, description="Service activation date")
    suspension_date: Optional[datetime] = Field(None, description="Service suspension date")
    termination_date: Optional[datetime] = Field(None, description="Service termination date")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    customer_name: Optional[str] = Field(None, description="Customer name")
    call_plan_name: Optional[str] = Field(None, description="Call plan name")
    monthly_fee: Optional[float] = Field(None, description="Monthly service fee")

    model_config = ConfigDict(from_attributes=True)

class VoiceServiceSummary(BaseModel):
    """Simplified Voice service schema for lists."""
    id: int
    customer_id: int
    customer_name: str
    call_plan_name: str
    status: VoiceServiceStatus
    phone_number: Optional[str] = None
    call_plan_type: CallPlanType
    monthly_fee: float
    activation_date: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class VoiceServiceList(BaseModel):
    """Schema for paginated Voice service list response."""
    services: List[VoiceServiceSummary]
    total: int = Field(..., description="Total number of services")
    page: Optional[int] = Field(None, description="Current page number")
    per_page: Optional[int] = Field(None, description="Items per page")
    pages: Optional[int] = Field(None, description="Total number of pages")


class VoiceServiceUsage(BaseModel):
    """Schema for Voice service usage data."""
    service_id: int
    period_start: datetime
    period_end: datetime
    outbound_minutes: int = Field(0, ge=0, description="Outbound call minutes")
    inbound_minutes: int = Field(0, ge=0, description="Inbound call minutes")
    total_minutes: int = Field(0, ge=0, description="Total call minutes")
    outbound_calls: int = Field(0, ge=0, description="Number of outbound calls")
    inbound_calls: int = Field(0, ge=0, description="Number of inbound calls")
    total_calls: int = Field(0, ge=0, description="Total number of calls")
    international_minutes: int = Field(0, ge=0, description="International call minutes")
    voicemail_messages: int = Field(0, ge=0, description="Number of voicemail messages")

    model_config = ConfigDict(from_attributes=True)

class VoiceServiceAnalytics(BaseModel):
    """Schema for Voice service analytics and reporting."""
    service_id: int
    customer_id: int
    current_month_usage: VoiceServiceUsage
    previous_month_usage: Optional[VoiceServiceUsage] = None
    usage_trend: str = Field(..., description="Usage trend: increasing, decreasing, stable")
    minute_limit_utilization: Optional[float] = Field(None, description="Percentage of minute limit used")
    average_call_duration: Optional[float] = Field(None, description="Average call duration in minutes")
    peak_usage_hour: Optional[int] = Field(None, ge=0, le=23, description="Peak usage hour of day")
    service_quality_score: Optional[float] = Field(None, ge=0, le=10, description="Service quality score")

    model_config = ConfigDict(from_attributes=True)