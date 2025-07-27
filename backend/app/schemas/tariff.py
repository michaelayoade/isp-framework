from ._base import BaseSchema
"""
ISP Tariff Schemas

Simple Pydantic schemas for tariff management aligned with ISP Framework vision.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import  Field


class InternetTariffBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    service_name: Optional[str] = Field(None, max_length=255)
    partners_ids: List[int] = Field(default_factory=list)
    
    # Pricing
    price: Decimal = Field(default=0, ge=0, decimal_places=4)
    with_vat: bool = True
    vat_percent: Decimal = Field(default=0, ge=0, le=100, decimal_places=2)
    
    # Speed Configuration (in kbps)
    speed_download: int = Field(..., gt=0, description="Download speed in kbps")
    speed_upload: int = Field(..., gt=0, description="Upload speed in kbps")
    speed_limit_at: int = Field(default=10, ge=0, le=100, description="Speed limit percentage")
    aggregation: int = Field(default=1, ge=1)
    
    # Burst Configuration
    burst_limit: int = Field(default=0, ge=0)
    burst_limit_fixed_down: int = Field(default=0, ge=0)
    burst_limit_fixed_up: int = Field(default=0, ge=0)
    burst_threshold: int = Field(default=0, ge=0)
    burst_threshold_fixed_down: int = Field(default=0, ge=0)
    burst_threshold_fixed_up: int = Field(default=0, ge=0)
    burst_time: int = Field(default=0, ge=0)
    burst_type: str = Field(default="none", regex="^(none|percent|fixed)$")
    
    # Speed Limit Configuration
    speed_limit_type: str = Field(default="none", regex="^(none|percent|fixed)$")
    speed_limit_fixed_down: int = Field(default=0, ge=0)
    speed_limit_fixed_up: int = Field(default=0, ge=0)
    
    # Billing Configuration
    billing_types: List[str] = Field(default_factory=list)
    
    # Status and availability
    is_active: bool = True
    is_public: bool = True
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None


class InternetTariffCreate(InternetTariffBase):
    pass


class InternetTariffUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    service_name: Optional[str] = Field(None, max_length=255)
    partners_ids: Optional[List[int]] = None
    
    # Pricing
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=4)
    with_vat: Optional[bool] = None
    vat_percent: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    
    # Speed Configuration
    speed_download: Optional[int] = Field(None, gt=0)
    speed_upload: Optional[int] = Field(None, gt=0)
    speed_limit_at: Optional[int] = Field(None, ge=0, le=100)
    aggregation: Optional[int] = Field(None, ge=1)
    
    # Burst Configuration
    burst_limit: Optional[int] = Field(None, ge=0)
    burst_limit_fixed_down: Optional[int] = Field(None, ge=0)
    burst_limit_fixed_up: Optional[int] = Field(None, ge=0)
    burst_threshold: Optional[int] = Field(None, ge=0)
    burst_threshold_fixed_down: Optional[int] = Field(None, ge=0)
    burst_threshold_fixed_up: Optional[int] = Field(None, ge=0)
    burst_time: Optional[int] = Field(None, ge=0)
    burst_type: Optional[str] = Field(None, regex="^(none|percent|fixed)$")
    
    # Speed Limit Configuration
    speed_limit_type: Optional[str] = Field(None, regex="^(none|percent|fixed)$")
    speed_limit_fixed_down: Optional[int] = Field(None, ge=0)
    speed_limit_fixed_up: Optional[int] = Field(None, ge=0)
    
    # Billing Configuration
    billing_types: Optional[List[str]] = None
    
    # Status and availability
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None


class InternetTariff(InternetTariffBase):
    id: int
    speed_display: str
    effective_price: Decimal
    has_burst: bool
    has_speed_limit: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TariffSearchFilters(BaseSchema):
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    partner_id: Optional[int] = None
    min_speed_download: Optional[int] = Field(None, ge=0)
    max_speed_download: Optional[int] = Field(None, ge=0)
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    billing_type: Optional[str] = None
    has_burst: Optional[bool] = None


class TariffListResponse(BaseSchema):
    tariffs: List[InternetTariff]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class TariffStatistics(BaseSchema):
    total_tariffs: int
    active_tariffs: int
    public_tariffs: int
    average_price: Decimal
    speed_ranges: dict  # min/max speeds
    billing_types_count: dict
