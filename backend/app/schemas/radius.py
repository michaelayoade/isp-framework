"""
RADIUS Session Management Schemas

This module contains Pydantic schemas for RADIUS session tracking,
customer online status, and network usage statistics.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# Enums for session management
class SessionStatus(str, Enum):
    ACTIVE = "active"
    STOPPED = "stopped"


class SessionType(str, Enum):
    MIKROTIK_API = "mikrotik_api"
    RADIUS = "radius"
    MANUAL = "manual"


class LoginType(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


# RADIUS Session Schemas
class RadiusSessionBase(BaseModel):
    customer_id: Optional[int] = None
    service_id: Optional[int] = None
    tariff_id: Optional[int] = None
    partner_id: Optional[int] = None
    nas_id: Optional[int] = None
    login: str = Field(..., max_length=255)
    username_real: Optional[str] = Field(None, max_length=255)
    in_bytes: int = Field(0, ge=0)
    out_bytes: int = Field(0, ge=0)
    start_session: datetime
    end_session: Optional[datetime] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = Field(None, max_length=17)
    call_to: Optional[str] = Field(None, max_length=50)
    port: Optional[str] = Field(None, max_length=50)
    price: Decimal = Field(Decimal("0"), ge=0)
    time_on: int = Field(0, ge=0)  # seconds
    type: SessionType = SessionType.MIKROTIK_API
    login_is: LoginType = LoginType.USER
    session_id: Optional[str] = Field(None, max_length=255)
    session_status: SessionStatus = SessionStatus.ACTIVE

    @field_validator("mac")
    def validate_mac_address(cls, v):
        if v is None:
            return v
        # Basic MAC address validation
        import re

        if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", v):
            raise ValueError("Invalid MAC address format")
        return v.upper()

    @field_validator("ipv4", "ipv6")
    def validate_ip_address(cls, v):
        if v is None:
            return v
        try:
            import ipaddress

            ipaddress.ip_address(v)
            return v
        except Exception:
            raise ValueError("Invalid IP address")


class RadiusSessionCreate(RadiusSessionBase):
    pass


class RadiusSessionUpdate(BaseModel):
    in_bytes: Optional[int] = Field(None, ge=0)
    out_bytes: Optional[int] = Field(None, ge=0)
    end_session: Optional[datetime] = None
    time_on: Optional[int] = Field(None, ge=0)
    session_status: Optional[SessionStatus] = None
    price: Optional[Decimal] = Field(None, ge=0)


class RadiusSession(RadiusSessionBase):
    id: int
    last_change: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_bytes: int
    session_duration_minutes: int


# Customer Online Schemas
class CustomerOnlineBase(BaseModel):
    customer_id: int
    service_id: Optional[int] = None
    tariff_id: Optional[int] = None
    partner_id: Optional[int] = None
    nas_id: Optional[int] = None
    login: str = Field(..., max_length=255)
    username_real: Optional[str] = Field(None, max_length=255)
    in_bytes: int = Field(0, ge=0)
    out_bytes: int = Field(0, ge=0)
    start_session: datetime
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = Field(None, max_length=17)
    call_to: Optional[str] = Field(None, max_length=50)
    port: Optional[str] = Field(None, max_length=50)
    price: Decimal = Field(Decimal("0"), ge=0)
    time_on: int = Field(0, ge=0)
    type: SessionType = SessionType.MIKROTIK_API
    login_is: LoginType = LoginType.USER
    session_id: str = Field(..., max_length=255)

    @field_validator("mac")
    def validate_mac_address(cls, v):
        if v is None:
            return v
        import re

        if not re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", v):
            raise ValueError("Invalid MAC address format")
        return v.upper()

    @field_validator("ipv4", "ipv6")
    def validate_ip_address(cls, v):
        if v is None:
            return v
        try:
            import ipaddress

            ipaddress.ip_address(v)
            return v
        except Exception:
            raise ValueError("Invalid IP address")


class CustomerOnlineCreate(CustomerOnlineBase):
    pass


class CustomerOnlineUpdate(BaseModel):
    in_bytes: Optional[int] = Field(None, ge=0)
    out_bytes: Optional[int] = Field(None, ge=0)
    time_on: Optional[int] = Field(None, ge=0)
    price: Optional[Decimal] = Field(None, ge=0)
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None


class CustomerOnline(CustomerOnlineBase):
    id: int
    last_change: datetime
    created_at: datetime
    total_bytes: int
    session_duration_minutes: int


# Customer Statistics Schemas
class CustomerStatisticsBase(BaseModel):
    customer_id: int
    service_id: Optional[int] = None
    tariff_id: Optional[int] = None
    partner_id: Optional[int] = None
    nas_id: Optional[int] = None
    login: Optional[str] = Field(None, max_length=255)
    in_bytes: int = Field(0, ge=0)
    out_bytes: int = Field(0, ge=0)
    start_date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_date: Optional[datetime] = None
    end_time: Optional[datetime] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    mac: Optional[str] = Field(None, max_length=17)
    call_to: Optional[str] = Field(None, max_length=50)
    port: Optional[str] = Field(None, max_length=50)
    price: Decimal = Field(Decimal("0"), ge=0)
    time_on: int = Field(0, ge=0)
    type: SessionType = SessionType.MIKROTIK_API
    login_is: LoginType = LoginType.USER
    period_type: PeriodType = PeriodType.DAILY
    period_start: datetime
    period_end: datetime


class CustomerStatisticsCreate(CustomerStatisticsBase):
    pass


class CustomerStatisticsUpdate(BaseModel):
    in_bytes: Optional[int] = Field(None, ge=0)
    out_bytes: Optional[int] = Field(None, ge=0)
    time_on: Optional[int] = Field(None, ge=0)
    price: Optional[Decimal] = Field(None, ge=0)
    period_end: Optional[datetime] = None


class CustomerStatistics(CustomerStatisticsBase):
    id: int
    last_change: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_bytes: int
    total_gb: float
    session_duration_hours: float


# Response schemas for lists and analytics
class RadiusSessionList(BaseModel):
    sessions: List[RadiusSession]
    total: int
    page: int
    per_page: int


class CustomerOnlineList(BaseModel):
    online_customers: List[CustomerOnline]
    total: int
    page: int
    per_page: int


class CustomerStatisticsList(BaseModel):
    statistics: List[CustomerStatistics]
    total: int
    page: int
    per_page: int


# Analytics and reporting schemas
class SessionAnalytics(BaseModel):
    total_sessions: int
    active_sessions: int
    stopped_sessions: int
    total_customers_online: int
    total_data_transferred_gb: float
    average_session_duration_minutes: float
    peak_concurrent_users: int


class CustomerUsageSummary(BaseModel):
    customer_id: int
    customer_name: Optional[str] = None
    total_sessions: int
    total_data_gb: float
    total_time_hours: float
    average_session_duration_minutes: float
    last_session: Optional[datetime] = None
    current_status: str  # online, offline


class NetworkUtilization(BaseModel):
    period_start: datetime
    period_end: datetime
    total_data_gb: float
    peak_concurrent_users: int
    average_concurrent_users: float
    total_session_time_hours: float
    unique_customers: int


class TopCustomersByUsage(BaseModel):
    customers: List[CustomerUsageSummary]
    period_start: datetime
    period_end: datetime
    total_customers: int
