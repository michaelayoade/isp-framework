from pydantic import BaseModel
"""
Reseller Management Schemas

Pydantic schemas for reseller management in single-tenant ISP Framework.
Resellers can manage their assigned customers with limited administrative access.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import  EmailStr, Field, ConfigDict


class ResellerBase(BaseModel):
    """Base reseller schema with common fields"""
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    contact_person: Optional[str] = Field(None, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    
    # Address
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="Nigeria", max_length=100)
    
    # Business Information
    tax_id: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    
    # Reseller Business Terms
    commission_percentage: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    territory: Optional[str] = Field(None, max_length=255)
    customer_limit: Optional[int] = Field(None, ge=0)
    
    # Status
    is_active: bool = Field(default=True)


class ResellerCreate(ResellerBase):
    """Schema for creating a new reseller"""
    password: str = Field(..., min_length=8, max_length=255, description="Password for reseller authentication")


class ResellerUpdate(BaseModel):
    """Schema for updating reseller information"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    
    # Address
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Business Information
    tax_id: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    
    # Reseller Business Terms
    commission_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    territory: Optional[str] = Field(None, max_length=255)
    customer_limit: Optional[int] = Field(None, ge=0)
    
    # Status
    is_active: Optional[bool] = None


class ResellerResponse(ResellerBase):
    """Schema for reseller response with additional fields"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    customer_count: Optional[int] = Field(default=0, description="Number of customers assigned to this reseller")
    total_commission: Optional[Decimal] = Field(default=Decimal("0"), description="Total commission earned")


class ResellerListResponse(BaseModel):
    """Schema for paginated reseller list response"""
    resellers: List[ResellerResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ResellerStats(BaseModel):
    """Schema for reseller statistics"""
    reseller_id: int
    reseller_name: str
    customer_count: int
    active_customers: int
    total_revenue: Decimal
    commission_earned: Decimal
    commission_percentage: Decimal
    territory: Optional[str] = None


class ResellerCommissionReport(BaseModel):
    """Schema for reseller commission reporting"""
    reseller_id: int
    reseller_name: str
    period_start: datetime
    period_end: datetime
    total_customer_payments: Decimal
    commission_rate: Decimal
    commission_amount: Decimal
    payment_count: int
    customer_count: int


class ResellerCustomerSummary(BaseModel):
    """Schema for reseller's customer summary"""
    customer_id: int
    portal_id: str
    name: str
    email: Optional[str] = None
    status: str
    services_count: int
    monthly_revenue: Decimal
    last_payment: Optional[datetime] = None
    created_at: datetime


class ResellerDashboard(BaseModel):
    """Schema for reseller dashboard data"""
    reseller: ResellerResponse
    stats: ResellerStats
    recent_customers: List[ResellerCustomerSummary]
    commission_summary: ResellerCommissionReport
