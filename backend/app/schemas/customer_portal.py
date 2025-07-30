"""
Customer Portal Schemas

Pydantic schemas for customer portal operations including sessions, payments,
service requests, dashboard data, and notifications.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SessionStatus(str, Enum):
    """Customer portal session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ServiceRequestStatus(str, Enum):
    """Service request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"


class NotificationStatus(str, Enum):
    """Notification status"""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


# Customer Portal Authentication Schemas
class CustomerPortalLoginRequest(BaseModel):
    """Schema for customer portal login request"""
    portal_id: str
    password: str


class CustomerPortalLoginResponse(BaseModel):
    """Schema for customer portal login response"""
    success: bool
    session_token: Optional[str] = None
    customer_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    message: str = "Login successful"


class CustomerPortalLogoutRequest(BaseModel):
    """Schema for customer portal logout request"""
    session_token: str


# Customer Portal Session Schemas
class CustomerPortalSessionBase(BaseModel):
    """Base schema for customer portal sessions"""
    customer_id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: SessionStatus = SessionStatus.ACTIVE


class CustomerPortalSessionCreate(CustomerPortalSessionBase):
    """Schema for creating customer portal session"""
    pass


class CustomerPortalSessionUpdate(BaseModel):
    """Schema for updating customer portal session"""
    status: Optional[SessionStatus] = None
    last_activity: Optional[datetime] = None


class CustomerPortalSessionResponse(CustomerPortalSessionBase):
    """Schema for customer portal session response"""
    id: int
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


# Customer Portal Payment Schemas
class CustomerPortalPaymentBase(BaseModel):
    """Base schema for customer portal payments"""
    customer_id: int
    amount: Decimal = Field(..., decimal_places=2)
    currency: str = "NGN"
    payment_method: str
    description: Optional[str] = None


class CustomerPortalPaymentRequest(BaseModel):
    """Schema for customer portal payment request"""
    amount: Decimal = Field(..., decimal_places=2, gt=0)
    currency: str = Field(default="NGN", max_length=3)
    payment_method: str
    description: Optional[str] = None


class CustomerPortalPaymentCreate(CustomerPortalPaymentBase):
    """Schema for creating customer portal payment"""
    pass


class CustomerPortalPaymentResponse(CustomerPortalPaymentBase):
    """Schema for customer portal payment response"""
    id: int
    payment_reference: str
    status: PaymentStatus
    gateway_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Customer Portal Service Request Schemas
class CustomerPortalServiceRequestBase(BaseModel):
    """Base schema for customer portal service requests"""
    customer_id: int
    request_type: str
    description: str
    requested_changes: Optional[Dict[str, Any]] = None


class CustomerPortalServiceRequestCreate(CustomerPortalServiceRequestBase):
    """Schema for creating customer portal service request"""
    pass


class CustomerPortalServiceRequestUpdate(BaseModel):
    """Schema for updating customer portal service request"""
    status: Optional[ServiceRequestStatus] = None
    admin_notes: Optional[str] = None
    approved_changes: Optional[Dict[str, Any]] = None


class CustomerPortalServiceRequestResponse(CustomerPortalServiceRequestBase):
    """Schema for customer portal service request response"""
    id: int
    status: ServiceRequestStatus
    admin_notes: Optional[str] = None
    approved_changes: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Customer Portal Dashboard Schemas
class CustomerPortalDashboardData(BaseModel):
    """Schema for customer portal dashboard data"""
    customer_info: Dict[str, Any]
    account_balance: Decimal
    active_services: List[Dict[str, Any]]
    recent_invoices: List[Dict[str, Any]]
    recent_payments: List[Dict[str, Any]]
    usage_summary: Dict[str, Any]
    notifications_count: int
    pending_requests: List[Dict[str, Any]]


class CustomerPortalDashboardResponse(BaseModel):
    """Schema for customer portal dashboard response"""
    success: bool = True
    data: CustomerPortalDashboardData
    message: str = "Dashboard data retrieved successfully"


# Customer Portal Notification Schemas
class CustomerPortalNotificationBase(BaseModel):
    """Base schema for customer portal notifications"""
    customer_id: int
    title: str
    message: str
    notification_type: str = "general"
    priority: str = "normal"


class CustomerPortalNotificationCreate(CustomerPortalNotificationBase):
    """Schema for creating customer portal notification"""
    pass


class CustomerPortalNotificationUpdate(BaseModel):
    """Schema for updating customer portal notification"""
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None


class CustomerPortalNotificationResponse(CustomerPortalNotificationBase):
    """Schema for customer portal notification response"""
    id: int
    status: NotificationStatus
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Customer Portal Preferences Schemas
class CustomerPortalPreferencesBase(BaseModel):
    """Base schema for customer portal preferences"""
    customer_id: int
    language: str = "en"
    timezone: str = "Africa/Lagos"
    email_notifications: bool = True
    sms_notifications: bool = True
    theme: str = "light"


class CustomerPortalPreferencesCreate(CustomerPortalPreferencesBase):
    """Schema for creating customer portal preferences"""
    pass


class CustomerPortalPreferencesUpdate(BaseModel):
    """Schema for updating customer portal preferences"""
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    theme: Optional[str] = None


class CustomerPortalPreferencesResponse(CustomerPortalPreferencesBase):
    """Schema for customer portal preferences response"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Search and Filter Schemas
class CustomerPortalSearchFilters(BaseModel):
    """Schema for customer portal search filters"""
    customer_id: Optional[int] = None
    status: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_term: Optional[str] = None


class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Schema for paginated responses"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

    @field_validator('pages', mode='before')
    @classmethod
    def calculate_pages(cls, v, info):
        # Get values from the data being validated
        data = info.data if hasattr(info, 'data') else {}
        total = data.get('total', 0)
        per_page = data.get('per_page', 10)
        return (total + per_page - 1) // per_page if per_page > 0 else 0


# Response Schemas
class CustomerPortalInvoiceResponse(BaseModel):
    """Schema for customer portal invoice response"""
    id: int
    invoice_number: str
    amount: Decimal
    due_date: datetime
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
    items: List[Dict[str, Any]] = []


class CustomerPortalUsageResponse(BaseModel):
    """Schema for customer portal usage response"""
    service_id: int
    service_name: str
    period: str
    data_used: Dict[str, Any]
    data_limit: Optional[Dict[str, Any]] = None
    percentage_used: float
    last_updated: datetime


class CustomerPortalFAQResponse(BaseModel):
    """Schema for customer portal FAQ response"""
    id: int
    question: str
    answer: str
    category: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerPortalActivityResponse(BaseModel):
    """Schema for customer portal activity response"""
    id: int
    action: str
    description: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class CustomerPortalResponse(BaseModel):
    """Generic customer portal response schema"""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class CustomerPortalErrorResponse(BaseModel):
    """Customer portal error response schema"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
