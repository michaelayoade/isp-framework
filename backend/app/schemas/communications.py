"""
Communications Schemas for ISP Framework

Pydantic schemas for communication templates, providers, logs, and preferences
with comprehensive validation and type safety.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from app.models.communications import (
    CommunicationType,
    CommunicationStatus,
    CommunicationPriority,
    TemplateCategory
)


# Base schemas
class CommunicationTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: TemplateCategory
    communication_type: CommunicationType
    subject_template: Optional[str] = None
    body_template: str = Field(..., min_length=1)
    html_template: Optional[str] = None
    is_active: bool = True
    language: str = Field(default="en", max_length=10)
    required_variables: List[str] = Field(default_factory=list)
    optional_variables: List[str] = Field(default_factory=list)
    sample_data: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)


class CommunicationTemplateCreate(CommunicationTemplateBase):
    pass


class CommunicationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[TemplateCategory] = None
    communication_type: Optional[CommunicationType] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = Field(None, min_length=1)
    html_template: Optional[str] = None
    is_active: Optional[bool] = None
    language: Optional[str] = Field(None, max_length=10)
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    sample_data: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)


class CommunicationTemplate(CommunicationTemplateBase):
    id: int
    is_system: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Communication Provider schemas
class CommunicationProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: CommunicationType
    provider_class: str = Field(..., min_length=1, max_length=255)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    credentials: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_default: bool = False
    priority: int = Field(default=100, ge=1, le=1000)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    rate_limit_per_hour: int = Field(default=1000, ge=1)
    rate_limit_per_day: int = Field(default=10000, ge=1)
    description: Optional[str] = None


class CommunicationProviderCreate(CommunicationProviderBase):
    pass


class CommunicationProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    provider_type: Optional[CommunicationType] = None
    provider_class: Optional[str] = Field(None, min_length=1, max_length=255)
    configuration: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_minute: Optional[int] = Field(None, ge=1)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)
    rate_limit_per_day: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None


class CommunicationProvider(CommunicationProviderBase):
    id: int
    success_rate: int
    average_delivery_time: int
    last_used: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Communication Log schemas
class CommunicationLogBase(BaseModel):
    communication_type: CommunicationType
    priority: CommunicationPriority = CommunicationPriority.NORMAL
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = Field(None, max_length=50)
    recipient_name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = Field(None, max_length=500)
    body: str = Field(..., min_length=1)
    html_body: Optional[str] = None
    context_type: Optional[str] = Field(None, max_length=50)
    context_id: Optional[int] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None

    @validator('recipient_email', 'recipient_phone')
    def validate_recipient(cls, v, values):
        if not v and not values.get('recipient_phone') and not values.get('recipient_email'):
            raise ValueError('At least one recipient method (email or phone) must be provided')
        return v


class CommunicationLogCreate(CommunicationLogBase):
    template_id: Optional[int] = None
    provider_id: Optional[int] = None
    customer_id: Optional[int] = None


class CommunicationLogUpdate(BaseModel):
    status: Optional[CommunicationStatus] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    provider_message_id: Optional[str] = Field(None, max_length=255)
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = Field(None, ge=0)


class CommunicationLog(CommunicationLogBase):
    id: int
    status: CommunicationStatus
    template_id: Optional[int]
    provider_id: Optional[int]
    customer_id: Optional[int]
    admin_id: Optional[int]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    provider_message_id: Optional[str]
    provider_response: Dict[str, Any]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Communication Queue schemas
class CommunicationQueueBase(BaseModel):
    queue_name: str = Field(..., min_length=1, max_length=255)
    communication_type: CommunicationType
    priority: CommunicationPriority = CommunicationPriority.NORMAL
    subject: Optional[str] = Field(None, max_length=500)
    body: str = Field(..., min_length=1)
    html_body: Optional[str] = None
    recipients: List[Dict[str, Any]] = Field(..., min_items=1)
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    batch_size: int = Field(default=100, ge=1, le=1000)
    delay_between_batches: int = Field(default=60, ge=0)


class CommunicationQueueCreate(CommunicationQueueBase):
    template_id: Optional[int] = None
    provider_id: Optional[int] = None


class CommunicationQueueUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|processing|completed|failed)$")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processed_count: Optional[int] = Field(None, ge=0)
    success_count: Optional[int] = Field(None, ge=0)
    failed_count: Optional[int] = Field(None, ge=0)


class CommunicationQueue(CommunicationQueueBase):
    id: int
    total_recipients: int
    processed_count: int
    success_count: int
    failed_count: int
    template_id: Optional[int]
    provider_id: Optional[int]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Communication Preferences schemas
class CommunicationPreferenceBase(BaseModel):
    email_enabled: bool = True
    email_billing: bool = True
    email_service_alerts: bool = True
    email_support: bool = True
    email_marketing: bool = False
    email_system: bool = True
    sms_enabled: bool = True
    sms_billing: bool = False
    sms_service_alerts: bool = True
    sms_support: bool = False
    sms_marketing: bool = False
    sms_system: bool = True
    push_enabled: bool = True
    push_billing: bool = True
    push_service_alerts: bool = True
    push_support: bool = True
    push_marketing: bool = False
    push_system: bool = True
    quiet_hours_start: str = Field(default="22:00", pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: str = Field(default="08:00", pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: str = Field(default="UTC", max_length=50)
    preferred_language: str = Field(default="en", max_length=10)


class CommunicationPreferenceCreate(CommunicationPreferenceBase):
    customer_id: int


class CommunicationPreferenceUpdate(CommunicationPreferenceBase):
    pass


class CommunicationPreference(CommunicationPreferenceBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Communication Rule schemas
class CommunicationRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_event: str = Field(..., min_length=1, max_length=100)
    trigger_conditions: Dict[str, Any] = Field(default_factory=dict)
    communication_type: CommunicationType
    priority: CommunicationPriority = CommunicationPriority.NORMAL
    delay_minutes: int = Field(default=0, ge=0)
    is_active: bool = True


class CommunicationRuleCreate(CommunicationRuleBase):
    template_id: int


class CommunicationRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_event: Optional[str] = Field(None, min_length=1, max_length=100)
    trigger_conditions: Optional[Dict[str, Any]] = None
    template_id: Optional[int] = None
    communication_type: Optional[CommunicationType] = None
    priority: Optional[CommunicationPriority] = None
    delay_minutes: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CommunicationRule(CommunicationRuleBase):
    id: int
    template_id: int
    triggered_count: int
    success_count: int
    failed_count: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Request/Response schemas
class SendCommunicationRequest(BaseModel):
    """Request to send a single communication"""
    communication_type: CommunicationType
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = Field(None, max_length=50)
    recipient_name: Optional[str] = Field(None, max_length=255)
    template_id: Optional[int] = None
    subject: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    html_body: Optional[str] = None
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    priority: CommunicationPriority = CommunicationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    customer_id: Optional[int] = None
    context_type: Optional[str] = Field(None, max_length=50)
    context_id: Optional[int] = None

    @validator('recipient_email', 'recipient_phone')
    def validate_recipient(cls, v, values):
        if not v and not values.get('recipient_phone') and not values.get('recipient_email'):
            raise ValueError('At least one recipient method (email or phone) must be provided')
        return v

    @validator('body')
    def validate_content(cls, v, values):
        if not v and not values.get('template_id'):
            raise ValueError('Either body content or template_id must be provided')
        return v


class SendCommunicationResponse(BaseModel):
    """Response after sending a communication"""
    communication_id: int
    status: CommunicationStatus
    message: str
    provider_message_id: Optional[str] = None


class BulkCommunicationRequest(BaseModel):
    """Request to send bulk communications"""
    queue_name: str = Field(..., min_length=1, max_length=255)
    communication_type: CommunicationType
    template_id: Optional[int] = None
    subject: Optional[str] = Field(None, max_length=500)
    body: Optional[str] = None
    html_body: Optional[str] = None
    recipients: List[Dict[str, Any]] = Field(..., min_items=1)
    template_variables: Dict[str, Any] = Field(default_factory=dict)
    priority: CommunicationPriority = CommunicationPriority.NORMAL
    scheduled_at: Optional[datetime] = None
    batch_size: int = Field(default=100, ge=1, le=1000)
    delay_between_batches: int = Field(default=60, ge=0)
    provider_id: Optional[int] = None


class BulkCommunicationResponse(BaseModel):
    """Response after queuing bulk communications"""
    queue_id: int
    total_recipients: int
    status: str
    message: str


class CommunicationStatsResponse(BaseModel):
    """Communication statistics response"""
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    average_delivery_time: int
    by_type: Dict[str, Dict[str, int]]
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class TemplateTestRequest(BaseModel):
    """Request to test a template"""
    template_id: int
    test_variables: Dict[str, Any] = Field(default_factory=dict)
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = Field(None, max_length=50)


class TemplateTestResponse(BaseModel):
    """Response from template testing"""
    rendered_subject: Optional[str]
    rendered_body: str
    rendered_html: Optional[str]
    validation_errors: List[str] = Field(default_factory=list)
    missing_variables: List[str] = Field(default_factory=list)


# Search and filter schemas
class CommunicationSearchFilters(BaseModel):
    """Search filters for communications"""
    communication_type: Optional[CommunicationType] = None
    status: Optional[CommunicationStatus] = None
    priority: Optional[CommunicationPriority] = None
    customer_id: Optional[int] = None
    template_id: Optional[int] = None
    provider_id: Optional[int] = None
    context_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None


class TemplateSearchFilters(BaseModel):
    """Search filters for templates"""
    category: Optional[TemplateCategory] = None
    communication_type: Optional[CommunicationType] = None
    is_active: Optional[bool] = None
    is_system: Optional[bool] = None
    language: Optional[str] = None
    search_term: Optional[str] = None


class ProviderSearchFilters(BaseModel):
    """Search filters for providers"""
    provider_type: Optional[CommunicationType] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    search_term: Optional[str] = None


# Pagination schemas
class PaginatedCommunicationLogs(BaseModel):
    """Paginated communication logs response"""
    items: List[CommunicationLog]
    total: int
    page: int
    size: int
    pages: int


class PaginatedTemplates(BaseModel):
    """Paginated templates response"""
    items: List[CommunicationTemplate]
    total: int
    page: int
    size: int
    pages: int


class PaginatedProviders(BaseModel):
    """Paginated providers response"""
    items: List[CommunicationProvider]
    total: int
    page: int
    size: int
    pages: int


class PaginatedQueues(BaseModel):
    """Paginated queues response"""
    items: List[CommunicationQueue]
    total: int
    page: int
    size: int
    pages: int
