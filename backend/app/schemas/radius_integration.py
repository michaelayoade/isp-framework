from pydantic import BaseModel

#!/usr/bin/env python3
"""
RADIUS Integration Schemas

Pydantic schemas for RADIUS authentication, session management,
and service integration API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator


class RadiusAuthRequest(BaseModel):
    """Schema for RADIUS authentication requests"""

    username: str = Field(
        ..., min_length=1, max_length=50, description="Customer username (portal ID)"
    )
    password: str = Field(
        ..., min_length=1, max_length=255, description="Customer password"
    )
    nas_ip: Optional[str] = Field(None, max_length=45, description="NAS IP address")
    nas_port: Optional[int] = Field(None, ge=0, description="NAS port number")


class RadiusAuthResponse(BaseModel):
    """Schema for RADIUS authentication responses"""

    authenticated: bool = Field(..., description="Authentication result")
    customer_id: int = Field(..., description="Customer ID")
    portal_id: str = Field(..., description="Customer portal ID")
    service_plan_id: int = Field(..., description="Active service plan ID")
    radius_attributes: Dict[str, Any] = Field(
        ..., description="RADIUS attributes for enforcement"
    )
    customer_info: Dict[str, Any] = Field(..., description="Customer information")


class RadiusSessionStart(BaseModel):
    """Schema for starting RADIUS sessions"""

    username: str = Field(
        ..., min_length=1, max_length=50, description="Customer username (portal ID)"
    )
    password: str = Field(
        ..., min_length=1, max_length=255, description="Customer password"
    )
    session_id: str = Field(
        ..., min_length=1, max_length=255, description="RADIUS session ID"
    )
    nas_ip: str = Field(..., max_length=45, description="NAS IP address")
    nas_port: Optional[int] = Field(None, ge=0, description="NAS port number")
    calling_station_id: Optional[str] = Field(
        None, max_length=50, description="Calling station ID"
    )
    called_station_id: Optional[str] = Field(
        None, max_length=50, description="Called station ID"
    )


class RadiusSessionStop(BaseModel):
    """Schema for stopping RADIUS sessions"""

    session_id: str = Field(
        ..., min_length=1, max_length=255, description="RADIUS session ID"
    )
    bytes_in: Optional[int] = Field(0, ge=0, description="Bytes received")
    bytes_out: Optional[int] = Field(0, ge=0, description="Bytes transmitted")
    packets_in: Optional[int] = Field(0, ge=0, description="Packets received")
    packets_out: Optional[int] = Field(0, ge=0, description="Packets transmitted")
    termination_cause: Optional[str] = Field(
        "User-Request", max_length=50, description="Session termination cause"
    )


class RadiusAccountingUpdate(BaseModel):
    """Schema for RADIUS accounting updates"""

    session_id: str = Field(
        ..., min_length=1, max_length=255, description="RADIUS session ID"
    )
    bytes_in: Optional[int] = Field(0, ge=0, description="Bytes received")
    bytes_out: Optional[int] = Field(0, ge=0, description="Bytes transmitted")
    packets_in: Optional[int] = Field(0, ge=0, description="Packets received")
    packets_out: Optional[int] = Field(0, ge=0, description="Packets transmitted")


class RadiusSessionResponse(BaseModel):
    """Schema for RADIUS session responses"""

    session_id: int = Field(..., description="Internal session ID")
    customer_id: int = Field(..., description="Customer ID")
    portal_id: str = Field(..., description="Customer portal ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    framed_ip_address: Optional[str] = Field(None, description="Assigned IP address")
    start_time: datetime = Field(..., description="Session start time")
    status: str = Field(..., description="Session status")
    radius_attributes: Dict[str, Any] = Field(..., description="RADIUS attributes")


class SessionInfo(BaseModel):
    """Schema for session information"""

    session_id: int = Field(..., description="Internal session ID")
    portal_id: str = Field(..., description="Customer portal ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    framed_ip_address: Optional[str] = Field(None, description="Assigned IP address")
    start_time: datetime = Field(..., description="Session start time")
    end_time: Optional[datetime] = Field(None, description="Session end time")
    status: str = Field(..., description="Session status")
    bytes_in: Optional[int] = Field(0, description="Bytes received")
    bytes_out: Optional[int] = Field(0, description="Bytes transmitted")
    session_duration: Optional[int] = Field(
        0, description="Session duration in seconds"
    )
    termination_cause: Optional[str] = Field(
        None, description="Session termination cause"
    )


class CustomerSessionsResponse(BaseModel):
    """Schema for customer sessions response"""

    customer_id: int = Field(..., description="Customer ID")
    total_sessions: int = Field(..., description="Total number of sessions")
    sessions: List[SessionInfo] = Field(..., description="List of sessions")


class ServiceEnforcementResponse(BaseModel):
    """Schema for service plan enforcement response"""

    service_plan_id: int = Field(..., description="Service plan ID")
    radius_attributes: Dict[str, Any] = Field(
        ..., description="RADIUS enforcement attributes"
    )


class ActiveSessionInfo(BaseModel):
    """Schema for active session information"""

    session_id: int = Field(..., description="Internal session ID")
    customer_id: int = Field(..., description="Customer ID")
    portal_id: str = Field(..., description="Customer portal ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    framed_ip_address: Optional[str] = Field(None, description="Assigned IP address")
    start_time: datetime = Field(..., description="Session start time")
    nas_ip_address: Optional[str] = Field(None, description="NAS IP address")
    nas_port: Optional[int] = Field(None, description="NAS port")
    bytes_in: Optional[int] = Field(0, description="Bytes received")
    bytes_out: Optional[int] = Field(0, description="Bytes transmitted")
    last_update: Optional[datetime] = Field(None, description="Last accounting update")


class ActiveSessionsResponse(BaseModel):
    """Schema for active sessions response"""

    total_active_sessions: int = Field(
        ..., description="Total number of active sessions"
    )
    sessions: List[ActiveSessionInfo] = Field(
        ..., description="List of active sessions"
    )


class RadiusStatisticsResponse(BaseModel):
    """Schema for RADIUS statistics response"""

    total_sessions: int = Field(..., description="Total number of sessions")
    active_sessions: int = Field(..., description="Number of active sessions")
    customers_online: int = Field(..., description="Number of customers online")
    total_bytes_in: int = Field(..., description="Total bytes received")
    total_bytes_out: int = Field(..., description="Total bytes transmitted")
    total_session_time: int = Field(..., description="Total session time in seconds")
    timestamp: datetime = Field(..., description="Statistics timestamp")


# Service Plan Integration Schemas


class ServicePlanEnforcementRequest(BaseModel):
    """Schema for service plan enforcement requests"""

    service_plan_id: int = Field(..., gt=0, description="Service plan ID")
    customer_id: Optional[int] = Field(
        None, gt=0, description="Customer ID for customer-specific attributes"
    )


class ServicePlanEnforcementResponse(BaseModel):
    """Schema for service plan enforcement response"""

    service_plan_id: int = Field(..., description="Service plan ID")
    service_plan_name: str = Field(..., description="Service plan name")
    service_type: str = Field(..., description="Service type")
    radius_attributes: Dict[str, Any] = Field(
        ..., description="RADIUS enforcement attributes"
    )
    bandwidth_limits: Optional[Dict[str, int]] = Field(
        None, description="Bandwidth limits"
    )
    data_limits: Optional[Dict[str, int]] = Field(None, description="Data usage limits")
    session_limits: Optional[Dict[str, int]] = Field(
        None, description="Session time limits"
    )


# IP Address Management Schemas


class IPAssignmentRequest(BaseModel):
    """Schema for IP address assignment requests"""

    customer_id: int = Field(..., gt=0, description="Customer ID")
    service_plan_id: int = Field(..., gt=0, description="Service plan ID")
    ip_type: str = Field("ipv4", pattern="^(ipv4|ipv6)$", description="IP address type")
    preferred_ip: Optional[str] = Field(None, description="Preferred IP address")


class IPAssignmentResponse(BaseModel):
    """Schema for IP address assignment response"""

    customer_id: int = Field(..., description="Customer ID")
    assigned_ip: str = Field(..., description="Assigned IP address")
    ip_type: str = Field(..., description="IP address type")
    network_id: int = Field(..., description="Network ID")
    assigned_at: datetime = Field(..., description="Assignment timestamp")
    lease_duration: Optional[int] = Field(None, description="Lease duration in seconds")


class IPReleaseRequest(BaseModel):
    """Schema for IP address release requests"""

    ip_address: str = Field(..., description="IP address to release")
    customer_id: Optional[int] = Field(None, description="Customer ID for verification")


# Usage Monitoring Schemas


class UsageMonitoringRequest(BaseModel):
    """Schema for usage monitoring requests"""

    customer_id: Optional[int] = Field(None, gt=0, description="Customer ID")
    service_plan_id: Optional[int] = Field(None, gt=0, description="Service plan ID")
    time_period: str = Field(
        "daily",
        pattern="^(hourly|daily|weekly|monthly)$",
        description="Monitoring period",
    )
    start_date: Optional[datetime] = Field(
        None, description="Start date for monitoring"
    )
    end_date: Optional[datetime] = Field(None, description="End date for monitoring")


class UsageStatistics(BaseModel):
    """Schema for usage statistics"""

    customer_id: int = Field(..., description="Customer ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    total_sessions: int = Field(..., description="Total number of sessions")
    total_bytes_in: int = Field(..., description="Total bytes received")
    total_bytes_out: int = Field(..., description="Total bytes transmitted")
    total_session_time: int = Field(..., description="Total session time in seconds")
    average_session_duration: int = Field(
        ..., description="Average session duration in seconds"
    )
    last_session: Optional[datetime] = Field(None, description="Last session timestamp")
    data_usage_percentage: Optional[float] = Field(
        None, description="Data usage as percentage of limit"
    )


class UsageMonitoringResponse(BaseModel):
    """Schema for usage monitoring response"""

    time_period: str = Field(..., description="Monitoring period")
    start_date: datetime = Field(..., description="Period start date")
    end_date: datetime = Field(..., description="Period end date")
    total_customers: int = Field(..., description="Total number of customers")
    usage_statistics: List[UsageStatistics] = Field(
        ..., description="Usage statistics per customer"
    )


# Network Integration Schemas


class NetworkProvisioningRequest(BaseModel):
    """Schema for network provisioning requests"""

    customer_id: int = Field(..., gt=0, description="Customer ID")
    service_plan_id: int = Field(..., gt=0, description="Service plan ID")
    router_id: Optional[int] = Field(None, gt=0, description="Target router ID")
    sector_id: Optional[int] = Field(None, gt=0, description="Target sector ID")
    provisioning_type: str = Field(
        "automatic", pattern="^(automatic|manual)$", description="Provisioning type"
    )


class NetworkProvisioningResponse(BaseModel):
    """Schema for network provisioning response"""

    customer_id: int = Field(..., description="Customer ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    provisioning_status: str = Field(..., description="Provisioning status")
    assigned_router: Optional[str] = Field(None, description="Assigned router")
    assigned_sector: Optional[str] = Field(None, description="Assigned sector")
    assigned_ip: Optional[str] = Field(None, description="Assigned IP address")
    provisioning_timestamp: datetime = Field(..., description="Provisioning timestamp")
    configuration_applied: bool = Field(
        ..., description="Whether configuration was applied"
    )


# Validation methods


@field_validator("portal_id")
def validate_portal_id(cls, v):
    """Validate portal ID format"""
    if not v or not v.strip():
        raise ValueError("Portal ID cannot be empty")
    return v.strip()


@field_validator("session_id")
def validate_session_id(cls, v):
    """Validate session ID format"""
    if not v or not v.strip():
        raise ValueError("Session ID cannot be empty")
    return v.strip()


# Add validators to relevant classes
RadiusAuthRequest.validate_portal_id = validate_portal_id
RadiusSessionStart.validate_portal_id = validate_portal_id
RadiusSessionStart.validate_session_id = validate_session_id
RadiusSessionStop.validate_session_id = validate_session_id
RadiusAccountingUpdate.validate_session_id = validate_session_id
