from pydantic import BaseModel
from pydantic import  Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.schemas.service_plan import ServicePlan
from app.schemas.customer_extended import CustomerExtendedResponse

# Basic customer response schema for customer service responses
class BasicCustomerResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    

class CustomerServiceBase(BaseModel):
    """Base customer service schema with common fields."""
    customer_id: int = Field(..., description="Customer ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    status: str = Field("active", description="Service status: active, suspended, terminated, pending")
    start_date: Optional[datetime] = Field(None, description="Service start date (defaults to now)")
    end_date: Optional[datetime] = Field(None, description="Service end date (null for ongoing)")
    custom_price: Optional[int] = Field(None, description="Custom price override in cents")
    discount_percentage: Optional[int] = Field(0, ge=0, le=100, description="Discount percentage (0-100)")
    
    @field_validator('status')
    def validate_status(cls, v):
        valid_statuses = ["active", "suspended", "terminated", "pending"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v


class CustomerServiceCreate(CustomerServiceBase):
    """Schema for creating a new customer service assignment."""
    pass


class CustomerServiceUpdate(BaseModel):
    """Schema for updating an existing customer service assignment."""
    status: Optional[str] = Field(None, description="Service status")
    end_date: Optional[datetime] = Field(None, description="Service end date")
    custom_price: Optional[int] = Field(None, description="Custom price override")
    discount_percentage: Optional[int] = Field(None, ge=0, le=100, description="Discount percentage")
    
    @field_validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["active", "suspended", "terminated", "pending"]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {valid_statuses}')
        return v


class CustomerServiceResponse(CustomerServiceBase):
    """Schema for customer service response with full details."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related objects (populated when requested)
    service_plan: Optional[ServicePlan] = None
    customer: Optional[BasicCustomerResponse] = None
    
    # Calculated fields
    effective_price: Optional[int] = Field(None, description="Effective price after discounts")
    monthly_cost: Optional[int] = Field(None, description="Monthly cost calculation")
    

class CustomerServiceSummary(BaseModel):
    """Summary schema for customer service (lightweight)."""
    id: int
    customer_id: int
    service_plan_id: int
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    effective_price: Optional[int] = None
    

class CustomerServiceSearch(BaseModel):
    """Schema for searching customer services."""
    customer_id: Optional[int] = Field(None, description="Filter by customer ID")
    service_plan_id: Optional[int] = Field(None, description="Filter by service plan ID")
    status: Optional[str] = Field(None, description="Filter by status")
    service_type: Optional[str] = Field(None, description="Filter by service plan type")
    active_only: bool = Field(True, description="Show only active services")
    include_expired: bool = Field(False, description="Include expired services")
    limit: int = Field(50, ge=1, le=100, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class CustomerServiceSearchResponse(BaseModel):
    """Response schema for customer service search."""
    services: List[CustomerServiceResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool
    

class ServiceProvisioningRequest(BaseModel):
    """Schema for service provisioning requests."""
    customer_id: int = Field(..., description="Customer ID")
    service_plan_id: int = Field(..., description="Service plan ID")
    start_date: Optional[datetime] = Field(None, description="Service start date")
    custom_price: Optional[int] = Field(None, description="Custom pricing")
    discount_percentage: Optional[int] = Field(0, ge=0, le=100, description="Discount percentage")
    notes: Optional[str] = Field(None, max_length=1000, description="Provisioning notes")


class ServiceProvisioningResponse(BaseModel):
    """Response schema for service provisioning."""
    customer_service: CustomerServiceResponse
    provisioning_status: str = Field(..., description="Provisioning status")
    provisioning_notes: Optional[str] = None
    estimated_activation: Optional[datetime] = None
    

class CustomerServicesOverview(BaseModel):
    """Overview schema for customer's all services."""
    customer_id: int
    total_services: int
    active_services: int
    suspended_services: int
    terminated_services: int
    total_monthly_cost: int
    services: List[CustomerServiceSummary]
    

class ServicePlanAssignments(BaseModel):
    """Schema showing all customers assigned to a service plan."""
    service_plan_id: int
    service_plan_name: str
    total_assignments: int
    active_assignments: int
    suspended_assignments: int
    assignments: List[CustomerServiceSummary]
    
