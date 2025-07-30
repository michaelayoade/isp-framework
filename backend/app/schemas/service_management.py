from ._base import BaseSchema
"""
Service Management Schemas - ISP Service Management System

Pydantic schemas for all modular service management operations including:
- Service templates (base, internet, voice, bundle)
- Customer service instances (base, internet, voice)
- Service provisioning workflows and templates
- Service lifecycle management (IP, status, suspension, usage, alerts)

Provides comprehensive validation and serialization for all service operations.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import  Field, field_validator
from enum import Enum

# Import service enums
from app.models.services.enums import (
    ServiceType, ServiceStatus, ProvisioningStatus, SuspensionReason,
    AlertSeverity, AlertStatus, UsageMetricType, IPAssignmentType,
    ProvisioningTaskStatus, ServiceQualityLevel
)


# ============================================================================
# Service Template Schemas
# ============================================================================

class ServiceTemplateBase(BaseSchema):
    """Base schema for service templates"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    service_type: ServiceType
    is_active: bool = True
    is_public: bool = True
    location_id: Optional[int] = None
    prerequisites: Optional[List[str]] = Field(default_factory=list)
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None


class ServiceTemplateCreate(ServiceTemplateBase):
    """Schema for creating service templates"""
    pass


class ServiceTemplateUpdate(BaseSchema):
    """Schema for updating service templates"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    location_id: Optional[int] = None
    prerequisites: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    effective_from: Optional[date] = None
    effective_until: Optional[date] = None


class ServiceTemplate(ServiceTemplateBase):
    """Schema for service template responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    

# Internet Service Template Schemas
class InternetServiceTemplateBase(BaseSchema):
    """Base schema for internet service templates"""
    template_id: int
    download_speed_kbps: int = Field(..., gt=0)
    upload_speed_kbps: int = Field(..., gt=0)
    data_limit_gb: Optional[int] = Field(None, gt=0)
    quality_level: ServiceQualityLevel = ServiceQualityLevel.STANDARD
    content_filtering: bool = False
    static_ip_included: bool = False
    router_included: bool = False
    installation_required: bool = True
    sla_uptime_percentage: Optional[Decimal] = Field(None, ge=90, le=100)


class InternetServiceTemplateCreate(InternetServiceTemplateBase):
    """Schema for creating internet service templates"""
    pass


class InternetServiceTemplateUpdate(BaseSchema):
    """Schema for updating internet service templates"""
    download_speed_kbps: Optional[int] = Field(None, gt=0)
    upload_speed_kbps: Optional[int] = Field(None, gt=0)
    data_limit_gb: Optional[int] = Field(None, gt=0)
    quality_level: Optional[ServiceQualityLevel] = None
    content_filtering: Optional[bool] = None
    static_ip_included: Optional[bool] = None
    router_included: Optional[bool] = None
    installation_required: Optional[bool] = None
    sla_uptime_percentage: Optional[Decimal] = Field(None, ge=90, le=100)


class InternetServiceTemplate(InternetServiceTemplateBase):
    """Schema for internet service template responses"""
    id: int
    template: ServiceTemplate
    

# Voice Service Template Schemas
class VoiceServiceTemplateBase(BaseSchema):
    """Base schema for voice service templates"""
    template_id: int
    included_minutes: Optional[int] = Field(None, gt=0)
    is_unlimited: bool = False
    international_calling: bool = False
    call_forwarding: bool = True
    voicemail: bool = True
    caller_id: bool = True
    call_waiting: bool = True
    conference_calling: bool = False
    supported_codecs: List[str] = Field(default_factory=lambda: ["G.711"])


class VoiceServiceTemplateCreate(VoiceServiceTemplateBase):
    """Schema for creating voice service templates"""
    pass


class VoiceServiceTemplateUpdate(BaseSchema):
    """Schema for updating voice service templates"""
    included_minutes: Optional[int] = Field(None, gt=0)
    is_unlimited: Optional[bool] = None
    international_calling: Optional[bool] = None
    call_forwarding: Optional[bool] = None
    voicemail: Optional[bool] = None
    caller_id: Optional[bool] = None
    call_waiting: Optional[bool] = None
    conference_calling: Optional[bool] = None
    supported_codecs: Optional[List[str]] = None


class VoiceServiceTemplate(VoiceServiceTemplateBase):
    """Schema for voice service template responses"""
    id: int
    template: ServiceTemplate
    

# Bundle Service Template Schemas
class BundleServiceTemplateBase(BaseSchema):
    """Base schema for bundle service templates"""
    template_id: int
    included_service_types: List[ServiceType]
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    minimum_contract_months: Optional[int] = Field(None, gt=0)
    early_termination_fee: Optional[Decimal] = Field(None, ge=0)
    bundle_benefits: Optional[List[str]] = Field(default_factory=list)


class BundleServiceTemplateCreate(BundleServiceTemplateBase):
    """Schema for creating bundle service templates"""
    pass


class BundleServiceTemplateUpdate(BaseSchema):
    """Schema for updating bundle service templates"""
    included_service_types: Optional[List[ServiceType]] = None
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    minimum_contract_months: Optional[int] = Field(None, gt=0)
    early_termination_fee: Optional[Decimal] = Field(None, ge=0)
    bundle_benefits: Optional[List[str]] = None


class BundleServiceTemplate(BundleServiceTemplateBase):
    """Schema for bundle service template responses"""
    id: int
    template: ServiceTemplate
    

# ============================================================================
# Customer Service Instance Schemas
# ============================================================================

class CustomerServiceBase(BaseSchema):
    """Base schema for customer services"""
    customer_id: int
    template_id: int
    status: ServiceStatus = ServiceStatus.PENDING
    activation_date: Optional[datetime] = None
    suspension_date: Optional[datetime] = None
    termination_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CustomerServiceCreate(CustomerServiceBase):
    """Schema for creating customer services"""
    pass


class CustomerServiceUpdate(BaseSchema):
    """Schema for updating customer services"""
    status: Optional[ServiceStatus] = None
    activation_date: Optional[datetime] = None
    suspension_date: Optional[datetime] = None
    termination_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    configuration: Optional[Dict[str, Any]] = None


class CustomerService(CustomerServiceBase):
    """Schema for customer service responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    

# Customer Internet Service Schemas
class CustomerInternetServiceBase(BaseSchema):
    """Base schema for customer internet services"""
    service_id: int
    pppoe_username: Optional[str] = Field(None, max_length=100)
    pppoe_password: Optional[str] = Field(None, max_length=100)
    assigned_ip: Optional[str] = Field(None, max_length=45)
    router_id: Optional[int] = None
    sector_id: Optional[int] = None
    current_download_speed: Optional[int] = Field(None, gt=0)
    current_upload_speed: Optional[int] = Field(None, gt=0)
    data_usage_gb: Optional[Decimal] = Field(None, ge=0)
    fup_exceeded: bool = False
    last_session_start: Optional[datetime] = None
    last_session_end: Optional[datetime] = None


class CustomerInternetServiceCreate(CustomerInternetServiceBase):
    """Schema for creating customer internet services"""
    pass


class CustomerInternetServiceUpdate(BaseSchema):
    """Schema for updating customer internet services"""
    pppoe_username: Optional[str] = Field(None, max_length=100)
    pppoe_password: Optional[str] = Field(None, max_length=100)
    assigned_ip: Optional[str] = Field(None, max_length=45)
    router_id: Optional[int] = None
    sector_id: Optional[int] = None
    current_download_speed: Optional[int] = Field(None, gt=0)
    current_upload_speed: Optional[int] = Field(None, gt=0)
    data_usage_gb: Optional[Decimal] = Field(None, ge=0)
    fup_exceeded: Optional[bool] = None
    last_session_start: Optional[datetime] = None
    last_session_end: Optional[datetime] = None


class CustomerInternetService(CustomerInternetServiceBase):
    """Schema for customer internet service responses"""
    id: int
    service: CustomerService
    

# Customer Voice Service Schemas
class CustomerVoiceServiceBase(BaseSchema):
    """Base schema for customer voice services"""
    service_id: int
    phone_number: Optional[str] = Field(None, max_length=20)
    sip_username: Optional[str] = Field(None, max_length=100)
    sip_password: Optional[str] = Field(None, max_length=100)
    sip_server: Optional[str] = Field(None, max_length=255)
    minutes_used: Optional[int] = Field(None, ge=0)
    minutes_remaining: Optional[int] = Field(None, ge=0)
    call_balance: Optional[Decimal] = Field(None, ge=0)
    last_call_date: Optional[datetime] = None
    total_calls_made: Optional[int] = Field(None, ge=0)
    total_call_duration_minutes: Optional[int] = Field(None, ge=0)


class CustomerVoiceServiceCreate(CustomerVoiceServiceBase):
    """Schema for creating customer voice services"""
    pass


class CustomerVoiceServiceUpdate(BaseSchema):
    """Schema for updating customer voice services"""
    phone_number: Optional[str] = Field(None, max_length=20)
    sip_username: Optional[str] = Field(None, max_length=100)
    sip_password: Optional[str] = Field(None, max_length=100)
    sip_server: Optional[str] = Field(None, max_length=255)
    minutes_used: Optional[int] = Field(None, ge=0)
    minutes_remaining: Optional[int] = Field(None, ge=0)
    call_balance: Optional[Decimal] = Field(None, ge=0)
    last_call_date: Optional[datetime] = None
    total_calls_made: Optional[int] = Field(None, ge=0)
    total_call_duration_minutes: Optional[int] = Field(None, ge=0)


class CustomerVoiceService(CustomerVoiceServiceBase):
    """Schema for customer voice service responses"""
    id: int
    service: CustomerService
    

# ============================================================================
# Service Provisioning Schemas
# ============================================================================

class ServiceProvisioningBase(BaseSchema):
    """Base schema for service provisioning"""
    service_id: int
    template_id: Optional[int] = None
    status: ProvisioningStatus = ProvisioningStatus.NOT_STARTED
    priority: int = Field(default=5, ge=1, le=10)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = Field(None, max_length=1000)
    rollback_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServiceProvisioningCreate(ServiceProvisioningBase):
    """Schema for creating service provisioning"""
    pass


class ServiceProvisioningUpdate(BaseSchema):
    """Schema for updating service provisioning"""
    status: Optional[ProvisioningStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = Field(None, max_length=1000)
    rollback_data: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None


class ServiceProvisioning(ServiceProvisioningBase):
    """Schema for service provisioning responses"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    

# Provisioning Template Schemas
class ProvisioningTemplateBase(BaseSchema):
    """Base schema for provisioning templates"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    service_type: ServiceType
    automation_level: int = Field(default=1, ge=1, le=5)
    requires_approval: bool = False
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    rollback_steps: List[Dict[str, Any]] = Field(default_factory=list)
    configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProvisioningTemplateCreate(ProvisioningTemplateBase):
    """Schema for creating provisioning templates"""
    pass


class ProvisioningTemplateUpdate(BaseSchema):
    """Schema for updating provisioning templates"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    automation_level: Optional[int] = Field(None, ge=1, le=5)
    requires_approval: Optional[bool] = None
    estimated_duration_minutes: Optional[int] = Field(None, gt=0)
    steps: Optional[List[Dict[str, Any]]] = None
    rollback_steps: Optional[List[Dict[str, Any]]] = None
    configuration: Optional[Dict[str, Any]] = None


class ProvisioningTemplate(ProvisioningTemplateBase):
    """Schema for provisioning template responses"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    

# ============================================================================
# Service Management Schemas
# ============================================================================

# Service IP Assignment Schemas
class ServiceIPAssignmentBase(BaseSchema):
    """Base schema for service IP assignments"""
    service_id: int
    ip_address: str = Field(..., max_length=45)
    assignment_type: IPAssignmentType
    network_id: Optional[int] = None
    mac_address: Optional[str] = Field(None, max_length=17)
    hostname: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    is_active: bool = True


class ServiceIPAssignmentCreate(ServiceIPAssignmentBase):
    """Schema for creating service IP assignments"""
    pass


class ServiceIPAssignmentUpdate(BaseSchema):
    """Schema for updating service IP assignments"""
    ip_address: Optional[str] = Field(None, max_length=45)
    assignment_type: Optional[IPAssignmentType] = None
    network_id: Optional[int] = None
    mac_address: Optional[str] = Field(None, max_length=17)
    hostname: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class ServiceIPAssignment(ServiceIPAssignmentBase):
    """Schema for service IP assignment responses"""
    id: int
    assigned_at: datetime
    updated_at: Optional[datetime] = None
    

# Service Status History Schemas
class ServiceStatusHistoryBase(BaseSchema):
    """Base schema for service status history"""
    service_id: int
    previous_status: Optional[ServiceStatus] = None
    new_status: ServiceStatus
    reason: Optional[str] = Field(None, max_length=500)
    is_automated: bool = False
    admin_id: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServiceStatusHistoryCreate(ServiceStatusHistoryBase):
    """Schema for creating service status history"""
    pass


class ServiceStatusHistory(ServiceStatusHistoryBase):
    """Schema for service status history responses"""
    id: int
    changed_at: datetime
    

# Service Suspension Schemas
class ServiceSuspensionBase(BaseSchema):
    """Base schema for service suspensions"""
    service_id: int
    reason: SuspensionReason
    grace_period_hours: Optional[int] = Field(None, gt=0)
    auto_restore_conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    escalation_level: int = Field(default=1, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)
    admin_id: Optional[int] = None


class ServiceSuspensionCreate(ServiceSuspensionBase):
    """Schema for creating service suspensions"""
    pass


class ServiceSuspensionUpdate(BaseSchema):
    """Schema for updating service suspensions"""
    grace_period_hours: Optional[int] = Field(None, gt=0)
    auto_restore_conditions: Optional[Dict[str, Any]] = None
    escalation_level: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)


class ServiceSuspension(ServiceSuspensionBase):
    """Schema for service suspension responses"""
    id: int
    suspended_at: datetime
    restored_at: Optional[datetime] = None
    is_active: bool
    

# Service Usage Tracking Schemas
class ServiceUsageTrackingBase(BaseSchema):
    """Base schema for service usage tracking"""
    service_id: int
    metric_type: UsageMetricType
    value: Decimal = Field(..., ge=0)
    unit: str = Field(..., max_length=20)
    recorded_at: datetime
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    quality_score: Optional[Decimal] = Field(None, ge=0, le=100)


class ServiceUsageTrackingCreate(ServiceUsageTrackingBase):
    """Schema for creating service usage tracking"""
    pass


class ServiceUsageTracking(ServiceUsageTrackingBase):
    """Schema for service usage tracking responses"""
    id: int
    

# Service Alert Schemas
class ServiceAlertBase(BaseSchema):
    """Base schema for service alerts"""
    service_id: int
    alert_type: str = Field(..., max_length=50)
    severity: AlertSeverity
    message: str = Field(..., max_length=1000)
    status: AlertStatus = AlertStatus.ACTIVE
    threshold_value: Optional[Decimal] = Field(None, ge=0)
    current_value: Optional[Decimal] = Field(None, ge=0)
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServiceAlertCreate(ServiceAlertBase):
    """Schema for creating service alerts"""
    pass


class ServiceAlertUpdate(BaseSchema):
    """Schema for updating service alerts"""
    status: Optional[AlertStatus] = None
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = Field(None, max_length=1000)


class ServiceAlert(ServiceAlertBase):
    """Schema for service alert responses"""
    id: int
    created_at: datetime
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    

# ============================================================================
# Search and Filter Schemas
# ============================================================================

class ServiceTemplateSearchFilters(BaseSchema):
    """Search filters for service templates"""
    service_type: Optional[ServiceType] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    location_id: Optional[int] = None
    effective_date: Optional[date] = None
    search_query: Optional[str] = None


class CustomerServiceSearchFilters(BaseSchema):
    """Search filters for customer services"""
    customer_id: Optional[int] = None
    template_id: Optional[int] = None
    status: Optional[ServiceStatus] = None
    service_type: Optional[ServiceType] = None
    activation_date_from: Optional[date] = None
    activation_date_to: Optional[date] = None
    search_query: Optional[str] = None


class ServiceProvisioningSearchFilters(BaseSchema):
    """Search filters for service provisioning"""
    service_id: Optional[int] = None
    status: Optional[ProvisioningStatus] = None
    priority_min: Optional[int] = Field(None, ge=1, le=10)
    priority_max: Optional[int] = Field(None, ge=1, le=10)
    scheduled_date_from: Optional[date] = None
    scheduled_date_to: Optional[date] = None


class ServiceAlertSearchFilters(BaseSchema):
    """Search filters for service alerts"""
    service_id: Optional[int] = None
    alert_type: Optional[str] = None
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None
    created_date_from: Optional[date] = None
    created_date_to: Optional[date] = None


# ============================================================================
# Statistics and Dashboard Schemas
# ============================================================================

class ServiceStatistics(BaseSchema):
    """Service statistics schema"""
    total_services: int = 0
    active_services: int = 0
    suspended_services: int = 0
    terminated_services: int = 0
    pending_services: int = 0
    services_by_type: Dict[str, int] = Field(default_factory=dict)
    monthly_activations: int = 0
    monthly_terminations: int = 0
    average_activation_time_hours: Optional[float] = None


class ProvisioningStatistics(BaseSchema):
    """Provisioning statistics schema"""
    total_provisioning_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_completion_time_minutes: Optional[float] = None
    success_rate_percentage: Optional[float] = None


class UsageStatistics(BaseSchema):
    """Usage statistics schema"""
    total_bandwidth_gb: Decimal = Field(default=Decimal('0'))
    average_usage_per_service_gb: Decimal = Field(default=Decimal('0'))
    peak_usage_gb: Decimal = Field(default=Decimal('0'))
    network_utilization_percentage: Optional[float] = None
    quality_score_average: Optional[float] = None


class AlertStatistics(BaseSchema):
    """Alert statistics schema"""
    total_alerts: int = 0
    active_alerts: int = 0
    critical_alerts: int = 0
    acknowledged_alerts: int = 0
    resolved_alerts: int = 0
    average_resolution_time_hours: Optional[float] = None


class ServiceDashboard(BaseSchema):
    """Comprehensive service dashboard schema"""
    service_stats: ServiceStatistics
    provisioning_stats: ProvisioningStatistics
    usage_stats: UsageStatistics
    alert_stats: AlertStatistics
    recent_alerts: List[ServiceAlert] = Field(default_factory=list)
    top_usage_services: List[Dict[str, Any]] = Field(default_factory=list)
    pending_provisioning: List[ServiceProvisioning] = Field(default_factory=list)


# ============================================================================
# Pagination and Response Schemas
# ============================================================================

class PaginationParams(BaseSchema):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseSchema):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    @field_validator('pages', mode='before')
    @classmethod
    def calculate_pages(cls, v, info):
        # Get values from the data being validated
        data = info.data if hasattr(info, 'data') else {}
        total = data.get('total', 0)
        size = data.get('size', 20)
        return (total + size - 1) // size if total > 0 else 0


# Response wrapper schemas
class ServiceTemplateListResponse(BaseSchema):
    """Service template list response"""
    items: List[ServiceTemplate]
    total: int
    page: int
    size: int
    pages: int


class CustomerServiceListResponse(BaseSchema):
    """Customer service list response"""
    items: List[CustomerService]
    total: int
    page: int
    size: int
    pages: int


class ServiceProvisioningListResponse(BaseSchema):
    """Service provisioning list response"""
    items: List[ServiceProvisioning]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# Bulk Operations Schemas
# ============================================================================

class BulkServiceOperation(BaseSchema):
    """Schema for bulk service operations"""
    service_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., max_length=50)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reason: Optional[str] = Field(None, max_length=500)
    admin_id: int


class BulkOperationResult(BaseSchema):
    """Schema for bulk operation results"""
    total_requested: int
    successful: int
    failed: int
    results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# Integration Schemas
# ============================================================================

class ServiceBillingIntegration(BaseSchema):
    """Schema for service billing integration"""
    service_id: int
    billing_account_id: Optional[int] = None
    monthly_charge: Optional[Decimal] = Field(None, ge=0)
    setup_fee: Optional[Decimal] = Field(None, ge=0)
    usage_charges: Optional[Decimal] = Field(None, ge=0)
    next_billing_date: Optional[date] = None
    billing_status: str = Field(default="active", max_length=20)


class ServiceNetworkIntegration(BaseSchema):
    """Schema for service network integration"""
    service_id: int
    router_id: Optional[int] = None
    sector_id: Optional[int] = None
    vlan_id: Optional[int] = None
    ip_pool_id: Optional[int] = None
    bandwidth_profile: Optional[str] = Field(None, max_length=100)
    qos_profile: Optional[str] = Field(None, max_length=100)


# Module metadata
__version__ = "1.0.0"
__author__ = "ISP Framework Team"
__description__ = "Comprehensive schemas for enhanced ISP service management"
