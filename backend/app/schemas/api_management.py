"""
API Management Schemas

Pydantic schemas for API management including:
- API Key management
- Usage analytics
- Rate limiting
- API documentation
- Quota management
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


class QuotaType(str, Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class APIVersionStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


# API Key Schemas
class APIKeyBase(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    permissions: Dict[str, Any] = Field(default_factory=dict)
    scopes: List[str] = Field(default_factory=list)
    rate_limit: int = Field(default=1000, ge=1, le=1000000)
    daily_quota: int = Field(default=10000, ge=1, le=10000000)
    monthly_quota: int = Field(default=100000, ge=1, le=100000000)
    expires_at: Optional[datetime] = None
    ip_whitelist: List[str] = Field(default_factory=list)
    referrer_whitelist: List[str] = Field(default_factory=list)
    user_agent_whitelist: List[str] = Field(default_factory=list)


class APIKeyCreate(APIKeyBase):
    partner_id: Optional[int] = None
    customer_id: Optional[int] = None
    admin_id: Optional[int] = None

    @field_validator("partner_id", "customer_id", "admin_id")
    def validate_owner(cls, v, values):
        # Ensure at least one owner is specified
        if not any(
            [
                values.get("partner_id"),
                values.get("customer_id"),
                values.get("admin_id"),
            ]
        ):
            raise ValueError(
                "At least one owner (partner_id, customer_id, or admin_id) must be specified"
            )
        return v


class APIKeyUpdate(BaseModel):
    key_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=1000000)
    daily_quota: Optional[int] = Field(None, ge=1, le=10000000)
    monthly_quota: Optional[int] = Field(None, ge=1, le=100000000)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    ip_whitelist: Optional[List[str]] = None
    referrer_whitelist: Optional[List[str]] = None
    user_agent_whitelist: Optional[List[str]] = None


class APIKeyResponse(APIKeyBase):
    id: int
    api_key: str
    api_secret: Optional[str] = None  # Only returned on creation
    partner_id: Optional[int] = None
    customer_id: Optional[int] = None
    admin_id: Optional[int] = None
    is_active: bool
    is_system: bool
    last_used: Optional[datetime] = None
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class APIKeyMinimal(BaseModel):
    id: int
    key_name: str
    api_key: str
    is_active: bool
    last_used: Optional[datetime] = None
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# API Usage Schemas
class APIUsageBase(BaseModel):
    endpoint: str
    method: HTTPMethod
    status_code: int
    response_time: float = Field(..., ge=0)
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    request_size: int = Field(default=0, ge=0)
    response_size: int = Field(default=0, ge=0)
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class APIUsageCreate(APIUsageBase):
    api_key_id: int


class APIUsageResponse(APIUsageBase):
    id: int
    api_key_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# API Version Schemas
class APIVersionBase(BaseModel):
    version: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_url: str = Field(..., min_length=1, max_length=500)
    status: APIVersionStatus = APIVersionStatus.ACTIVE
    is_default: bool = False
    documentation_url: Optional[str] = None
    changelog: Optional[str] = None
    deprecated_at: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    migration_guide: Optional[str] = None


class APIVersionCreate(APIVersionBase):
    pass


class APIVersionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[APIVersionStatus] = None
    is_default: Optional[bool] = None
    documentation_url: Optional[str] = None
    changelog: Optional[str] = None
    deprecated_at: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    migration_guide: Optional[str] = None


class APIVersionResponse(APIVersionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# API Endpoint Schemas
class APIEndpointBase(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)
    method: HTTPMethod
    operation_id: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    example_request: Optional[Dict[str, Any]] = None
    example_response: Optional[Dict[str, Any]] = None
    is_deprecated: bool = False
    requires_auth: bool = True
    required_scopes: List[str] = Field(default_factory=list)
    average_response_time: float = Field(default=0, ge=0)


class APIEndpointCreate(APIEndpointBase):
    api_version_id: int


class APIEndpointUpdate(BaseModel):
    summary: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    example_request: Optional[Dict[str, Any]] = None
    example_response: Optional[Dict[str, Any]] = None
    is_deprecated: Optional[bool] = None
    requires_auth: Optional[bool] = None
    required_scopes: Optional[List[str]] = None
    average_response_time: Optional[float] = Field(None, ge=0)


class APIEndpointResponse(APIEndpointBase):
    id: int
    api_version_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# API Quota Schemas
class APIQuotaBase(BaseModel):
    quota_type: QuotaType
    period_start: datetime
    period_end: datetime
    request_limit: int = Field(..., ge=1)
    response_limit: int = Field(default=0, ge=0)


class APIQuotaCreate(APIQuotaBase):
    api_key_id: int


class APIQuotaUpdate(BaseModel):
    request_limit: Optional[int] = Field(None, ge=1)
    response_limit: Optional[int] = Field(None, ge=0)


class APIQuotaResponse(APIQuotaBase):
    id: int
    api_key_id: int
    requests_used: int = 0
    responses_sent: int = 0
    is_exceeded: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Rate Limit Schemas
class APIRateLimitBase(BaseModel):
    window_start: datetime
    window_end: datetime
    request_count: int = Field(default=0, ge=0)


class APIRateLimitCreate(APIRateLimitBase):
    api_key_id: int


class APIRateLimitResponse(APIRateLimitBase):
    id: int
    api_key_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Analytics and Reporting Schemas
class APIUsageAnalytics(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    unique_endpoints: int
    unique_users: int

    # Time-based breakdown
    requests_by_hour: Dict[str, int]
    requests_by_day: Dict[str, int]
    requests_by_endpoint: Dict[str, int]

    # Error analysis
    error_breakdown: Dict[str, int]
    status_code_distribution: Dict[int, int]

    # Performance metrics
    response_time_percentiles: Dict[str, float]


class APIKeyUsageReport(BaseModel):
    api_key_id: int
    key_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    quota_usage: Dict[str, float]
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


# Request/Response Schemas
class APIKeyFilter(BaseModel):
    partner_id: Optional[int] = None
    customer_id: Optional[int] = None
    admin_id: Optional[int] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class APIUsageFilter(BaseModel):
    api_key_id: Optional[int] = None
    endpoint: Optional[str] = None
    method: Optional[HTTPMethod] = None
    status_code: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class APIKeyTestRequest(BaseModel):
    endpoint: str = Field(..., min_length=1)
    method: HTTPMethod = HTTPMethod.GET
    test_data: Optional[Dict[str, Any]] = None


class APIKeyTestResponse(BaseModel):
    success: bool
    status_code: int
    response_time: float
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# List Response Schemas
class APIKeyListResponse(BaseModel):
    items: List[APIKeyResponse]
    total: int
    page: int
    pages: int
    limit: int


class APIUsageListResponse(BaseModel):
    items: List[APIUsageResponse]
    total: int
    page: int
    pages: int
    limit: int


class APIQuotaListResponse(BaseModel):
    items: List[APIQuotaResponse]
    total: int
    page: int
    pages: int
    limit: int


class APIEndpointListResponse(BaseModel):
    items: List[APIEndpointResponse]
    total: int
    page: int
    pages: int
    limit: int


class APIVersionListResponse(BaseModel):
    items: List[APIVersionResponse]
    total: int
    page: int
    pages: int
    limit: int


class UsageAnalyticsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    unique_endpoints: int
    unique_users: int
    requests_by_hour: Dict[str, int]
    requests_by_day: Dict[str, int]
    requests_by_endpoint: Dict[str, int]
    error_breakdown: Dict[str, int]
    status_code_distribution: Dict[int, int]
    response_time_percentiles: Dict[str, float]


class RateLimitStatus(BaseModel):
    is_limited: bool
    remaining_requests: int
    reset_time: datetime
    window_duration: int
    current_count: int
    limit: int


class QuotaStatus(BaseModel):
    is_exceeded: bool
    requests_used: int
    requests_remaining: int
    quota_limit: int
    period_start: datetime
    period_end: datetime


class APIQuotaStatus(BaseModel):
    """API quota status with daily and monthly usage tracking"""

    key_id: int
    daily_used: int
    daily_limit: int
    daily_remaining: int
    monthly_used: int
    monthly_limit: int
    monthly_remaining: int


class APIKeyUsageStats(BaseModel):
    api_key_id: int
    key_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    quota_usage: Dict[str, float]
    last_used: Optional[datetime]
    daily_usage: Dict[str, int]
    monthly_usage: Dict[str, int]
