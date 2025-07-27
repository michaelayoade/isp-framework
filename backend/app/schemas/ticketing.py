"""
Ticketing System Pydantic Schemas
Request/response models for ticketing API endpoints
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# Enums for validation
class TicketTypeEnum(str, Enum):
    SUPPORT = "support"
    TECHNICAL = "technical"
    INCIDENT = "incident"
    MAINTENANCE = "maintenance"
    FIELD_WORK = "field_work"
    ABUSE = "abuse"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"


class TicketPriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatusEnum(str, Enum):
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_VENDOR = "pending_vendor"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketSourceEnum(str, Enum):
    CUSTOMER_PORTAL = "customer_portal"
    PHONE = "phone"
    EMAIL = "email"
    CHAT = "chat"
    WALK_IN = "walk_in"
    SYSTEM_AUTOMATED = "system_automated"
    MONITORING = "monitoring"
    STAFF = "staff"
    API = "api"


class EscalationReasonEnum(str, Enum):
    SLA_BREACH = "sla_breach"
    CUSTOMER_REQUEST = "customer_request"
    COMPLEXITY = "complexity"
    MANAGER_DECISION = "manager_decision"
    REPEATED_ISSUE = "repeated_issue"


class FieldWorkStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


# Base schemas
class TicketBase(BaseModel):
    ticket_type: TicketTypeEnum
    category: Optional[str] = None
    subcategory: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    priority: TicketPriorityEnum = TicketPriorityEnum.NORMAL
    urgency: int = Field(3, ge=1, le=5)
    impact: int = Field(3, ge=1, le=5)
    work_location: Optional[str] = None
    gps_latitude: Optional[str] = None
    gps_longitude: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}


class TicketCreate(TicketBase):
    customer_id: Optional[int] = None
    service_id: Optional[int] = None
    contact_id: Optional[int] = None
    source: TicketSourceEnum = TicketSourceEnum.CUSTOMER_PORTAL
    source_reference: Optional[str] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[TicketPriorityEnum] = None
    urgency: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    work_location: Optional[str] = None
    gps_latitude: Optional[str] = None
    gps_longitude: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    initial_diagnosis: Optional[str] = None
    resolution_summary: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatusEnum
    reason: Optional[str] = None


class TicketAssignment(BaseModel):
    assigned_to: int
    assigned_team: Optional[str] = None


class TicketResponse(TicketBase):
    id: int
    ticket_number: str
    status: TicketStatusEnum
    customer_id: Optional[int]
    service_id: Optional[int]
    contact_id: Optional[int]
    assigned_to: Optional[int]
    assigned_team: Optional[str]
    assigned_at: Optional[datetime]
    source: TicketSourceEnum
    source_reference: Optional[str]
    sla_policy_id: Optional[int]
    due_date: Optional[datetime]
    first_response_due: Optional[datetime]
    resolution_due: Optional[datetime]
    first_response_at: Optional[datetime]
    first_response_sla_met: Optional[bool]
    resolution_sla_met: Optional[bool]
    initial_diagnosis: Optional[str]
    resolution_summary: Optional[str]
    customer_satisfaction: Optional[int]
    customer_feedback: Optional[str]
    estimated_hours: Optional[Decimal]
    actual_hours: Optional[Decimal]
    auto_created: bool
    monitoring_alert_id: Optional[str]
    external_ticket_reference: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    # Computed properties
    is_overdue: Optional[bool] = None
    sla_time_remaining_hours: Optional[float] = None
    response_time_hours: Optional[float] = None
    resolution_time_hours: Optional[float] = None

    class Config:
        from_attributes = True


# Message schemas
class TicketMessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    message_type: str = "comment"
    subject: Optional[str] = None
    content_format: str = "text"
    is_internal: bool = False
    is_solution: bool = False


class TicketMessageCreate(TicketMessageBase):
    author_type: str  # customer, agent, system
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class TicketMessageResponse(TicketMessageBase):
    id: int
    ticket_id: int
    author_type: str
    author_id: Optional[int]
    author_name: Optional[str]
    author_email: Optional[str]
    is_auto_generated: bool
    email_sent: bool
    sms_sent: bool
    push_notification_sent: bool
    email_message_id: Optional[str]
    external_reference: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Escalation schemas
class TicketEscalationCreate(BaseModel):
    escalation_reason: EscalationReasonEnum
    escalation_level: int = 1
    escalated_to: int
    escalated_to_team: Optional[str] = None
    escalation_notes: Optional[str] = None
    urgency_justification: Optional[str] = None


class TicketEscalationResponse(BaseModel):
    id: int
    ticket_id: int
    escalation_reason: EscalationReasonEnum
    escalation_level: int
    escalated_from: Optional[int]
    escalated_to: int
    escalated_from_team: Optional[str]
    escalated_to_team: Optional[str]
    escalation_notes: Optional[str]
    urgency_justification: Optional[str]
    response_notes: Optional[str]
    response_action: Optional[str]
    responded_at: Optional[datetime]
    responded_by: Optional[int]
    is_active: bool
    escalated_at: datetime

    class Config:
        from_attributes = True


# Field Work schemas
class FieldWorkOrderBase(BaseModel):
    work_type: str = Field(..., min_length=1)
    work_description: str = Field(..., min_length=1)
    special_instructions: Optional[str] = None
    work_address: str = Field(..., min_length=1)
    gps_latitude: Optional[str] = None
    gps_longitude: Optional[str] = None
    location_contact_name: Optional[str] = None
    location_contact_phone: Optional[str] = None
    priority: TicketPriorityEnum = TicketPriorityEnum.NORMAL
    scheduled_date: Optional[datetime] = None
    estimated_duration_hours: Optional[Decimal] = None
    required_equipment: List[str] = []
    required_materials: List[str] = []
    customer_availability: Optional[str] = None
    access_requirements: Optional[str] = None
    safety_requirements: Optional[str] = None


class FieldWorkOrderCreate(FieldWorkOrderBase):
    assigned_technician: Optional[int] = None
    technician_team: Optional[str] = None


class FieldWorkOrderUpdate(BaseModel):
    work_description: Optional[str] = None
    special_instructions: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    estimated_duration_hours: Optional[Decimal] = None
    assigned_technician: Optional[int] = None
    technician_team: Optional[str] = None
    status: Optional[FieldWorkStatusEnum] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    work_performed: Optional[str] = None
    findings: Optional[str] = None
    work_completed: Optional[bool] = None
    customer_satisfaction_score: Optional[int] = Field(None, ge=1, le=5)


class FieldWorkOrderResponse(FieldWorkOrderBase):
    id: int
    ticket_id: int
    work_order_number: str
    status: FieldWorkStatusEnum
    assigned_technician: Optional[int]
    technician_team: Optional[str]
    backup_technician: Optional[int]
    equipment_assigned: List[str]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    work_performed: Optional[str]
    findings: Optional[str]
    work_completed: bool
    customer_signature_required: bool
    customer_signature_obtained: bool
    customer_satisfaction_score: Optional[int]
    before_photos: List[str]
    after_photos: List[str]
    work_photos: List[str]
    follow_up_required: bool
    follow_up_date: Optional[datetime]
    follow_up_reason: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Computed properties
    is_overdue: Optional[bool] = None
    actual_duration_hours: Optional[float] = None

    class Config:
        from_attributes = True


# Time Entry schemas
class TicketTimeEntryCreate(BaseModel):
    hours_worked: Decimal = Field(..., gt=0)
    work_description: str = Field(..., min_length=1)
    work_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TicketTimeEntryResponse(BaseModel):
    id: int
    ticket_id: int
    hours_worked: Decimal
    work_description: str
    work_type: Optional[str]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    worked_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# SLA Policy schemas
class SLAPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    ticket_types: List[str] = []
    customer_types: List[str] = []
    first_response_time: int = Field(..., gt=0)  # minutes
    critical_resolution_time: int = Field(..., gt=0)
    urgent_resolution_time: int = Field(..., gt=0)
    high_resolution_time: int = Field(..., gt=0)
    normal_resolution_time: int = Field(..., gt=0)
    low_resolution_time: int = Field(..., gt=0)
    auto_escalate_enabled: bool = True
    escalation_threshold_percent: int = Field(80, ge=1, le=100)
    business_hours_only: bool = False
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    business_days: List[int] = [1, 2, 3, 4, 5]
    timezone: str = "UTC"
    is_default: bool = False


class SLAPolicyResponse(SLAPolicyCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Knowledge Base schemas
class KnowledgeBaseArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    summary: Optional[str] = Field(None, max_length=500)
    content: str = Field(..., min_length=1)
    content_format: str = "html"
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = []
    keywords: List[str] = []
    ticket_types: List[str] = []
    service_types: List[str] = []
    difficulty_level: Optional[str] = None
    is_public: bool = False


class KnowledgeBaseArticleResponse(KnowledgeBaseArticleCreate):
    id: int
    author_id: Optional[int]
    reviewer_id: Optional[int]
    status: str
    view_count: int
    helpful_votes: int
    not_helpful_votes: int
    version: str
    previous_version_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    helpfulness_ratio: Optional[float] = None

    class Config:
        from_attributes = True


# Search and filter schemas
class TicketSearchFilters(BaseModel):
    customer_id: Optional[int] = None
    assigned_to: Optional[int] = None
    status: Optional[TicketStatusEnum] = None
    priority: Optional[TicketPriorityEnum] = None
    ticket_type: Optional[TicketTypeEnum] = None
    category: Optional[str] = None
    overdue: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search_text: Optional[str] = None


class TicketStatisticsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    overdue_tickets: int
    resolved_tickets: int
    sla_performance: Dict[str, Union[int, float]]
    average_response_time_hours: float
    average_resolution_time_hours: float
    customer_satisfaction: float


class PaginatedTicketResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedMessageResponse(BaseModel):
    messages: List[TicketMessageResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# Incident schemas
class NetworkIncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    incident_type: Optional[str] = None
    severity: str = "medium"
    affected_devices: List[int] = []
    affected_networks: List[str] = []
    affected_services: List[str] = []
    affected_locations: List[int] = []
    impact_radius_km: Optional[Decimal] = None
    estimated_customers_affected: int = 0
    detected_at: datetime
    incident_commander: Optional[int] = None
    response_team: List[int] = []


class NetworkIncidentResponse(NetworkIncidentCreate):
    id: int
    incident_number: str
    confirmed_customers_affected: int
    business_customers_affected: int
    residential_customers_affected: int
    reported_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    status: str
    root_cause: Optional[str]
    corrective_actions: Optional[str]
    preventive_actions: Optional[str]
    customer_notification_sent: bool
    status_page_updated: bool
    vendor_ticket_numbers: List[str]
    monitoring_alert_ids: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_downtime_minutes: Optional[float] = None

    class Config:
        from_attributes = True


# Template schemas
class TicketTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    ticket_type: TicketTypeEnum
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: TicketPriorityEnum = TicketPriorityEnum.NORMAL
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    auto_assign_team: Optional[str] = None
    auto_assign_agent: Optional[int] = None
    sla_policy_id: Optional[int] = None
    require_customer_info: bool = True
    require_service_info: bool = False
    require_location_info: bool = False
    custom_fields_required: List[str] = []
    default_custom_fields: Dict[str, Any] = {}
    is_public: bool = False


class TicketTemplateResponse(TicketTemplateCreate):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
