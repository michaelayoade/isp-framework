"""Dashboard schemas for request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class MetricResponse(BaseModel):
    """Response schema for individual metrics."""
    metric_key: str
    metric_name: str
    value: Optional[Union[int, float]]
    unit: Optional[str]
    display_format: str
    category: str
    period: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    calculated_at: str
    error: Optional[str] = None

    class Config:
        from_attributes = True


class KPIResponse(BaseModel):
    """Response schema for KPI collections."""
    kpis: Dict[str, MetricResponse]
    period: str
    start_date: Optional[str]
    end_date: Optional[str]
    segments: List[str]
    calculated_at: str

    class Config:
        from_attributes = True


class FinancialReportResponse(BaseModel):
    """Response schema for financial reports."""
    summary: Dict[str, MetricResponse]
    breakdown: Optional[Dict[str, Any]]
    period: str
    start_date: Optional[str]
    end_date: Optional[str]
    generated_at: str

    class Config:
        from_attributes = True


class NetworkReportResponse(BaseModel):
    """Response schema for network reports."""
    summary: Dict[str, MetricResponse]
    period: str
    start_date: Optional[str]
    end_date: Optional[str]
    generated_at: str

    class Config:
        from_attributes = True


class DashboardWidgetResponse(BaseModel):
    """Response schema for dashboard widgets."""
    widget_key: str
    title: str
    description: Optional[str]
    category: str
    widget_type: str
    chart_type: Optional[str]
    metrics: List[str]
    display_config: Optional[Dict[str, Any]]
    position: Optional[Dict[str, Any]]
    refresh_interval_seconds: int
    auto_refresh: bool

    class Config:
        from_attributes = True


class MetricDefinitionResponse(BaseModel):
    """Response schema for metric definitions."""
    metric_key: str
    metric_name: str
    description: Optional[str]
    category: str
    calculation_method: str
    display_format: str
    unit: Optional[str]
    is_real_time: bool
    cache_ttl_seconds: int

    class Config:
        from_attributes = True


class SegmentDefinitionResponse(BaseModel):
    """Response schema for segment definitions."""
    segment_key: str
    segment_name: str
    description: Optional[str]
    segment_type: str
    criteria: Dict[str, Any]

    class Config:
        from_attributes = True


# Request schemas for creating/updating dashboard configurations

class MetricDefinitionCreate(BaseModel):
    """Schema for creating metric definitions."""
    metric_key: str = Field(..., min_length=1, max_length=100)
    metric_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(financial|network|customer|operational)$")
    calculation_method: str = Field(..., pattern="^(sum|avg|count|ratio|custom_sql)$")
    source_table: Optional[str] = Field(None, max_length=100)
    source_column: Optional[str] = Field(None, max_length=100)
    custom_sql: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    joins: Optional[List[Dict[str, Any]]] = None
    display_format: str = Field("number", pattern="^(currency|percentage|number|bytes)$")
    unit: Optional[str] = Field(None, max_length=20)
    decimal_places: int = Field(2, ge=0, le=10)
    cache_ttl_seconds: int = Field(300, ge=0, le=86400)
    is_real_time: bool = False
    visibility_roles: Optional[List[str]] = None
    tenant_scope: str = Field("reseller", pattern="^(global|reseller|customer)$")

    @validator('custom_sql')
    def validate_custom_sql(cls, v, values):
        if values.get('calculation_method') == 'custom_sql' and not v:
            raise ValueError('custom_sql is required when calculation_method is custom_sql')
        return v

    @validator('source_table', 'source_column')
    def validate_source_fields(cls, v, values):
        if values.get('calculation_method') in ['sum', 'avg', 'count'] and not v:
            raise ValueError(f'{cls.__name__} is required for standard calculation methods')
        return v


class MetricDefinitionUpdate(BaseModel):
    """Schema for updating metric definitions."""
    metric_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    calculation_method: Optional[str] = Field(None, pattern="^(sum|avg|count|ratio|custom_sql)$")
    source_table: Optional[str] = Field(None, max_length=100)
    source_column: Optional[str] = Field(None, max_length=100)
    custom_sql: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    joins: Optional[List[Dict[str, Any]]] = None
    display_format: Optional[str] = Field(None, pattern="^(currency|percentage|number|bytes)$")
    unit: Optional[str] = Field(None, max_length=20)
    decimal_places: Optional[int] = Field(None, ge=0, le=10)
    cache_ttl_seconds: Optional[int] = Field(None, ge=0, le=86400)
    is_real_time: Optional[bool] = None
    visibility_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SegmentDefinitionCreate(BaseModel):
    """Schema for creating segment definitions."""
    segment_key: str = Field(..., min_length=1, max_length=100)
    segment_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    segment_type: str = Field(..., pattern="^(customer|service|geographic|device|custom)$")
    criteria: Dict[str, Any] = Field(..., min_items=1)
    base_table: Optional[str] = Field(None, max_length=100)
    join_tables: Optional[List[Dict[str, Any]]] = None
    visibility_roles: Optional[List[str]] = None
    tenant_scope: str = Field("reseller", pattern="^(global|reseller|customer)$")


class SegmentDefinitionUpdate(BaseModel):
    """Schema for updating segment definitions."""
    segment_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = Field(None, min_items=1)
    base_table: Optional[str] = Field(None, max_length=100)
    join_tables: Optional[List[Dict[str, Any]]] = None
    visibility_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class DashboardWidgetCreate(BaseModel):
    """Schema for creating dashboard widgets."""
    widget_key: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(financial|network|customer|operational)$")
    widget_type: str = Field(..., pattern="^(chart|metric|table|gauge|map|custom)$")
    chart_type: Optional[str] = Field(None, pattern="^(line|bar|pie|donut|area|scatter|heatmap)$")
    metrics: List[str] = Field(..., min_items=1)
    display_config: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None
    available_segments: Optional[List[str]] = None
    refresh_interval_seconds: int = Field(300, ge=30, le=3600)
    auto_refresh: bool = True
    visibility_roles: Optional[List[str]] = None
    tenant_scope: str = Field("reseller", pattern="^(global|reseller|customer)$")


class DashboardWidgetUpdate(BaseModel):
    """Schema for updating dashboard widgets."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    widget_type: Optional[str] = Field(None, pattern="^(chart|metric|table|gauge|map|custom)$")
    chart_type: Optional[str] = Field(None, pattern="^(line|bar|pie|donut|area|scatter|heatmap)$")
    metrics: Optional[List[str]] = Field(None, min_items=1)
    display_config: Optional[Dict[str, Any]] = None
    position: Optional[Dict[str, Any]] = None
    default_filters: Optional[Dict[str, Any]] = None
    available_segments: Optional[List[str]] = None
    refresh_interval_seconds: Optional[int] = Field(None, ge=30, le=3600)
    auto_refresh: Optional[bool] = None
    visibility_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ThresholdDefinitionCreate(BaseModel):
    """Schema for creating threshold definitions."""
    threshold_key: str = Field(..., min_length=1, max_length=100)
    threshold_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    metric_key: str = Field(..., min_length=1, max_length=100)
    operator: str = Field(..., pattern="^(>|<|>=|<=|=|!=|between)$")
    value: float
    secondary_value: Optional[float] = None
    severity: str = Field(..., pattern="^(critical|warning|info)$")
    category: str = Field(..., pattern="^(performance|financial|security|operational)$")
    alert_config: Dict[str, Any] = Field(..., min_items=1)
    evaluation_interval_seconds: int = Field(300, ge=60, le=3600)
    consecutive_breaches_required: int = Field(1, ge=1, le=10)
    cooldown_seconds: int = Field(1800, ge=300, le=86400)
    filters: Optional[Dict[str, Any]] = None
    segments: Optional[List[str]] = None
    visibility_roles: Optional[List[str]] = None
    tenant_scope: str = Field("reseller", pattern="^(global|reseller|customer)$")

    @validator('secondary_value')
    def validate_secondary_value(cls, v, values):
        if values.get('operator') == 'between' and v is None:
            raise ValueError('secondary_value is required when operator is between')
        return v


class ThresholdDefinitionUpdate(BaseModel):
    """Schema for updating threshold definitions."""
    threshold_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    operator: Optional[str] = Field(None, pattern="^(>|<|>=|<=|=|!=|between)$")
    value: Optional[float] = None
    secondary_value: Optional[float] = None
    severity: Optional[str] = Field(None, pattern="^(critical|warning|info)$")
    category: Optional[str] = Field(None, pattern="^(performance|financial|security|operational)$")
    alert_config: Optional[Dict[str, Any]] = Field(None, min_items=1)
    evaluation_interval_seconds: Optional[int] = Field(None, ge=60, le=3600)
    consecutive_breaches_required: Optional[int] = Field(None, ge=1, le=10)
    cooldown_seconds: Optional[int] = Field(None, ge=300, le=86400)
    filters: Optional[Dict[str, Any]] = None
    segments: Optional[List[str]] = None
    visibility_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


# Query parameter schemas

class KPIQueryParams(BaseModel):
    """Query parameters for KPI endpoints."""
    categories: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    period: str = Field("month", pattern="^(day|week|month|quarter|year)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    segments: Optional[List[str]] = None

    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v and v <= start_date:
            raise ValueError('end_date must be after start_date')
        return v


class ReportQueryParams(BaseModel):
    """Query parameters for report endpoints."""
    period: str = Field("month", pattern="^(day|week|month|quarter|year)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    breakdown_by: Optional[str] = None

    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v and v <= start_date:
            raise ValueError('end_date must be after start_date')
        return v
