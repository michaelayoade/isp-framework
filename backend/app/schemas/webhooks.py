"""
Webhook System Schemas

Pydantic schemas for webhook API validation and serialization.
"""

from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from app.models.webhooks.enums import (
    WebhookStatus, DeliveryStatus, EventCategory, FilterOperator,
    RetryStrategy, SignatureAlgorithm, HttpMethod, ContentType
)


# Base Schemas
class WebhookEventTypeBase(BaseModel):
    """Base schema for webhook event types"""
    name: str = Field(..., max_length=100, description="Event name (e.g., customer.created)")
    category: EventCategory
    description: Optional[str] = None
    payload_schema: Optional[Dict[str, Any]] = None
    sample_payload: Optional[Dict[str, Any]] = None
    is_active: bool = True
    requires_authentication: bool = True
    max_retry_attempts: int = Field(default=5, ge=1, le=10)


class WebhookEventTypeCreate(WebhookEventTypeBase):
    """Schema for creating webhook event types"""
    pass


class WebhookEventTypeUpdate(BaseModel):
    """Schema for updating webhook event types"""
    name: Optional[str] = Field(None, max_length=100)
    category: Optional[EventCategory] = None
    description: Optional[str] = None
    payload_schema: Optional[Dict[str, Any]] = None
    sample_payload: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    requires_authentication: Optional[bool] = None
    max_retry_attempts: Optional[int] = Field(None, ge=1, le=10)


class WebhookEventTypeResponse(WebhookEventTypeBase):
    """Schema for webhook event type responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Webhook Endpoint Schemas
class WebhookEndpointBase(BaseModel):
    """Base schema for webhook endpoints"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    url: HttpUrl
    http_method: HttpMethod = HttpMethod.POST
    content_type: ContentType = ContentType.JSON
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    verify_ssl: bool = True
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retry_attempts: int = Field(default=5, ge=1, le=10)
    retry_delay_seconds: int = Field(default=60, ge=1, le=3600)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=10000)
    enable_filtering: bool = False


class WebhookEndpointCreate(WebhookEndpointBase):
    """Schema for creating webhook endpoints"""
    secret_token: Optional[str] = Field(None, min_length=16, max_length=255)
    signature_algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256
    subscribed_event_ids: List[int] = Field(default_factory=list)


class WebhookEndpointUpdate(BaseModel):
    """Schema for updating webhook endpoints"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    http_method: Optional[HttpMethod] = None
    content_type: Optional[ContentType] = None
    custom_headers: Optional[Dict[str, str]] = None
    verify_ssl: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)
    retry_strategy: Optional[RetryStrategy] = None
    max_retry_attempts: Optional[int] = Field(None, ge=1, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=1, le=3600)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=10000)
    enable_filtering: Optional[bool] = None
    status: Optional[WebhookStatus] = None
    is_active: Optional[bool] = None


class WebhookEndpointResponse(WebhookEndpointBase):
    """Schema for webhook endpoint responses"""
    id: int
    status: WebhookStatus
    is_active: bool
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    last_delivery_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    subscribed_events: List[WebhookEventTypeResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Webhook Filter Schemas
class WebhookFilterBase(BaseModel):
    """Base schema for webhook filters"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    field_path: str = Field(..., max_length=500, description="JSON path to field")
    operator: FilterOperator
    value: Optional[str] = Field(None, max_length=1000)
    values: Optional[List[str]] = None
    include_on_match: bool = True
    is_active: bool = True

    @validator('values')
    def validate_values_for_operator(cls, v, values):
        operator = values.get('operator')
        if operator in [FilterOperator.IN, FilterOperator.NOT_IN] and not v:
            raise ValueError(f"'values' is required for operator {operator}")
        return v


class WebhookFilterCreate(WebhookFilterBase):
    """Schema for creating webhook filters"""
    pass


class WebhookFilterUpdate(BaseModel):
    """Schema for updating webhook filters"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    field_path: Optional[str] = Field(None, max_length=500)
    operator: Optional[FilterOperator] = None
    value: Optional[str] = Field(None, max_length=1000)
    values: Optional[List[str]] = None
    include_on_match: Optional[bool] = None
    is_active: Optional[bool] = None


class WebhookFilterResponse(WebhookFilterBase):
    """Schema for webhook filter responses"""
    id: int
    endpoint_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Webhook Event Schemas
class WebhookEventBase(BaseModel):
    """Base schema for webhook events"""
    event_type_id: int
    payload: Dict[str, Any]
    event_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    occurred_at: datetime


class WebhookEventCreate(WebhookEventBase):
    """Schema for creating webhook events"""
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    triggered_by_user_id: Optional[int] = None
    triggered_by_customer_id: Optional[int] = None


class WebhookEventResponse(WebhookEventBase):
    """Schema for webhook event responses"""
    id: int
    event_id: str
    is_processed: bool
    processed_at: Optional[datetime] = None
    created_at: datetime
    event_type: WebhookEventTypeResponse

    class Config:
        from_attributes = True


# Webhook Delivery Schemas
class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery responses"""
    id: int
    delivery_id: str
    status: DeliveryStatus
    attempt_count: int
    max_attempts: int
    scheduled_at: datetime
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    response_status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookDeliveryAttemptResponse(BaseModel):
    """Schema for webhook delivery attempt responses"""
    id: int
    attempt_number: int
    attempted_at: datetime
    response_status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    dns_resolution_time_ms: Optional[int] = None
    connection_time_ms: Optional[int] = None
    ssl_handshake_time_ms: Optional[int] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    is_successful: bool

    class Config:
        from_attributes = True


# Search and Filter Schemas
class WebhookEndpointSearch(BaseModel):
    """Schema for searching webhook endpoints"""
    name: Optional[str] = None
    status: Optional[WebhookStatus] = None
    is_active: Optional[bool] = None
    url_contains: Optional[str] = None
    event_type_id: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_delivery_after: Optional[datetime] = None
    last_delivery_before: Optional[datetime] = None


class WebhookEventSearch(BaseModel):
    """Schema for searching webhook events"""
    event_type_id: Optional[int] = None
    category: Optional[EventCategory] = None
    is_processed: Optional[bool] = None
    occurred_after: Optional[datetime] = None
    occurred_before: Optional[datetime] = None
    triggered_by_user_id: Optional[int] = None
    triggered_by_customer_id: Optional[int] = None


class WebhookDeliverySearch(BaseModel):
    """Schema for searching webhook deliveries"""
    endpoint_id: Optional[int] = None
    event_id: Optional[int] = None
    status: Optional[DeliveryStatus] = None
    scheduled_after: Optional[datetime] = None
    scheduled_before: Optional[datetime] = None
    delivered_after: Optional[datetime] = None
    delivered_before: Optional[datetime] = None
    min_attempts: Optional[int] = None
    max_attempts: Optional[int] = None


# Statistics and Analytics Schemas
class WebhookEndpointStats(BaseModel):
    """Schema for webhook endpoint statistics"""
    endpoint_id: int
    endpoint_name: str
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    average_response_time_ms: Optional[float] = None
    last_delivery_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None


class WebhookSystemStats(BaseModel):
    """Schema for overall webhook system statistics"""
    total_endpoints: int
    active_endpoints: int
    total_event_types: int
    total_events_today: int
    total_deliveries_today: int
    successful_deliveries_today: int
    failed_deliveries_today: int
    average_success_rate: float
    events_by_category: Dict[str, int]
    top_endpoints: List[WebhookEndpointStats]


# Bulk Operations Schemas
class WebhookEndpointBulkUpdate(BaseModel):
    """Schema for bulk updating webhook endpoints"""
    endpoint_ids: List[int]
    updates: WebhookEndpointUpdate


class WebhookEventBulkCreate(BaseModel):
    """Schema for bulk creating webhook events"""
    events: List[WebhookEventCreate]


# Test and Validation Schemas
class WebhookTestRequest(BaseModel):
    """Schema for testing webhook endpoints"""
    endpoint_id: int
    test_payload: Dict[str, Any]
    override_url: Optional[HttpUrl] = None


class WebhookTestResponse(BaseModel):
    """Schema for webhook test responses"""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None


# Pagination Schemas
class PaginatedWebhookEndpoints(BaseModel):
    """Paginated webhook endpoints response"""
    items: List[WebhookEndpointResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedWebhookEvents(BaseModel):
    """Paginated webhook events response"""
    items: List[WebhookEventResponse]
    total: int
    page: int
    size: int
    pages: int


class PaginatedWebhookDeliveries(BaseModel):
    """Paginated webhook deliveries response"""
    items: List[WebhookDeliveryResponse]
    total: int
    page: int
    size: int
    pages: int
