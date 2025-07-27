from ._base import BaseSchema
"""
Service Management Schemas

This module contains Pydantic schemas for service management:
Internet services, Voice services, Bundle services, and Recurring services.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import  Field, validator


# Internet Service Schemas
class InternetServiceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    download_speed: int = Field(..., gt=0, description="Download speed in Mbps")
    upload_speed: int = Field(..., gt=0, description="Upload speed in Mbps")
    data_limit: Optional[int] = Field(None, gt=0, description="Data limit in GB, null for unlimited")
    monthly_price: Decimal = Field(..., gt=0)
    setup_fee: Decimal = Field(0, ge=0)
    cancellation_fee: Decimal = Field(0, ge=0)
    router_id: Optional[int] = None
    sector_id: Optional[int] = None
    ip_pool_id: Optional[int] = None
    is_active: bool = True
    is_public: bool = True
    priority: int = Field(0, ge=0)
    radius_profile: Optional[str] = Field(None, max_length=100)
    bandwidth_limit_down: Optional[str] = Field(None, max_length=50)
    bandwidth_limit_up: Optional[str] = Field(None, max_length=50)
    activation_method: str = Field("manual", pattern="^(manual|auto)$")
    provisioning_script: Optional[str] = None


class InternetServiceCreate(InternetServiceBase):
    pass


class InternetServiceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    download_speed: Optional[int] = Field(None, gt=0)
    upload_speed: Optional[int] = Field(None, gt=0)
    data_limit: Optional[int] = Field(None, gt=0)
    monthly_price: Optional[Decimal] = Field(None, gt=0)
    setup_fee: Optional[Decimal] = Field(None, ge=0)
    cancellation_fee: Optional[Decimal] = Field(None, ge=0)
    router_id: Optional[int] = None
    sector_id: Optional[int] = None
    ip_pool_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    radius_profile: Optional[str] = Field(None, max_length=100)
    bandwidth_limit_down: Optional[str] = Field(None, max_length=50)
    bandwidth_limit_up: Optional[str] = Field(None, max_length=50)
    activation_method: Optional[str] = Field(None, pattern="^(manual|auto)$")
    provisioning_script: Optional[str] = None


class InternetService(InternetServiceBase):
    id: int
    speed_display: str
    data_limit_display: str
    created_at: datetime
    updated_at: Optional[datetime]


# Voice Service Schemas
class VoiceServiceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    included_minutes: int = Field(0, ge=0)
    per_minute_rate: Decimal = Field(..., gt=0)
    monthly_price: Decimal = Field(..., gt=0)
    setup_fee: Decimal = Field(0, ge=0)
    cancellation_fee: Decimal = Field(0, ge=0)
    codec: str = Field("G.711", max_length=50)
    quality: str = Field("standard", pattern="^(standard|premium)$")
    is_active: bool = True
    is_public: bool = True
    priority: int = Field(0, ge=0)
    route_prefix: Optional[str] = Field(None, max_length=20)
    gateway_id: Optional[int] = None


class VoiceServiceCreate(VoiceServiceBase):
    pass


class VoiceServiceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    included_minutes: Optional[int] = Field(None, ge=0)
    per_minute_rate: Optional[Decimal] = Field(None, gt=0)
    monthly_price: Optional[Decimal] = Field(None, gt=0)
    setup_fee: Optional[Decimal] = Field(None, ge=0)
    cancellation_fee: Optional[Decimal] = Field(None, ge=0)
    codec: Optional[str] = Field(None, max_length=50)
    quality: Optional[str] = Field(None, pattern="^(standard|premium)$")
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    route_prefix: Optional[str] = Field(None, max_length=20)
    gateway_id: Optional[int] = None


class VoiceService(VoiceServiceBase):
    id: int
    minutes_display: str
    created_at: datetime
    updated_at: Optional[datetime]


# Bundle Service Schemas
class BundleServiceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    internet_service_id: Optional[int] = None
    voice_service_id: Optional[int] = None
    bundle_price: Decimal = Field(..., gt=0)
    individual_price: Optional[Decimal] = Field(None, gt=0)
    discount_amount: Decimal = Field(0, ge=0)
    discount_percentage: Decimal = Field(0, ge=0, le=100)
    is_active: bool = True
    is_public: bool = True
    priority: int = Field(0, ge=0)
    minimum_term_months: int = Field(12, gt=0)
    early_termination_fee: Decimal = Field(0, ge=0)


class BundleServiceCreate(BundleServiceBase):
    pass


class BundleServiceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    internet_service_id: Optional[int] = None
    voice_service_id: Optional[int] = None
    bundle_price: Optional[Decimal] = Field(None, gt=0)
    individual_price: Optional[Decimal] = Field(None, gt=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    minimum_term_months: Optional[int] = Field(None, gt=0)
    early_termination_fee: Optional[Decimal] = Field(None, ge=0)


class BundleService(BundleServiceBase):
    id: int
    savings_amount: Decimal
    savings_percentage: float
    created_at: datetime
    updated_at: Optional[datetime]
    internet_service: Optional[InternetService] = None
    voice_service: Optional[VoiceService] = None


# Recurring Service Schemas
class RecurringServiceBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    service_type: str = Field(..., pattern="^(addon|maintenance|support)$")
    billing_cycle: str = Field("monthly", pattern="^(monthly|quarterly|yearly)$")
    price: Decimal = Field(..., gt=0)
    setup_fee: Decimal = Field(0, ge=0)
    is_active: bool = True
    is_public: bool = True
    is_addon: bool = True
    auto_provision: bool = False
    provisioning_script: Optional[str] = None


class RecurringServiceCreate(RecurringServiceBase):
    pass


class RecurringServiceUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    service_type: Optional[str] = Field(None, pattern="^(addon|maintenance|support)$")
    billing_cycle: Optional[str] = Field(None, pattern="^(monthly|quarterly|yearly)$")
    price: Optional[Decimal] = Field(None, gt=0)
    setup_fee: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    is_addon: Optional[bool] = None
    auto_provision: Optional[bool] = None
    provisioning_script: Optional[str] = None


class RecurringService(RecurringServiceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]


# Service Tariff Schemas
class ServiceTariffBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tariff_type: str = Field(..., pattern="^(internet|voice|bundle|recurring)$")
    service_id: int = Field(..., gt=0)
    base_price: Decimal = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    billing_cycle: str = Field("monthly", pattern="^(monthly|quarterly|yearly)$")
    has_usage_limits: bool = False
    overage_rate: Decimal = Field(0, ge=0)
    promotional_price: Optional[Decimal] = Field(None, gt=0)
    promotion_end_date: Optional[datetime] = None
    is_active: bool = True
    is_default: bool = False
    requires_approval: bool = False
    available_regions: Optional[str] = None


class ServiceTariffCreate(ServiceTariffBase):
    pass


class ServiceTariffUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tariff_type: Optional[str] = Field(None, pattern="^(internet|voice|bundle|recurring)$")
    service_id: Optional[int] = Field(None, gt=0)
    base_price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    billing_cycle: Optional[str] = Field(None, pattern="^(monthly|quarterly|yearly)$")
    has_usage_limits: Optional[bool] = None
    overage_rate: Optional[Decimal] = Field(None, ge=0)
    promotional_price: Optional[Decimal] = Field(None, gt=0)
    promotion_end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    requires_approval: Optional[bool] = None
    available_regions: Optional[str] = None


class ServiceTariff(ServiceTariffBase):
    id: int
    current_price: Decimal
    created_at: datetime
    updated_at: Optional[datetime]


# Service Management Overview Schemas
class ServiceOverview(BaseSchema):
    """Overview of all service types and counts"""
    internet_services: int
    voice_services: int
    bundle_services: int
    recurring_services: int
    total_services: int
    active_services: int
    public_services: int


class ServiceSearchFilters(BaseSchema):
    """Filters for service search and listing"""
    service_type: Optional[str] = Field(None, pattern="^(internet|voice|bundle|recurring)$")
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    search_term: Optional[str] = Field(None, min_length=1)


class ServiceListResponse(BaseSchema):
    """Response for service listing with pagination"""
    services: List[dict]  # Mixed service types
    total: int
    page: int
    size: int
    pages: int
