from pydantic import BaseModel
from pydantic import Field
from typing import Optional
from datetime import datetime


class BillingTypeBase(BaseModel):
    """Base schema for billing types."""
    code: str = Field(..., min_length=1, max_length=50, description="Billing type code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=255, description="Optional description")
    is_active: bool = Field(True, description="Is billing type active")
    sort_order: int = Field(0, description="Sort order for UI")
    
    # Billing properties
    is_recurring: bool = Field(True, description="Is this a recurring billing model")
    requires_prepayment: bool = Field(False, description="Must customer prepay")
    supports_prorating: bool = Field(True, description="Can be prorated for partial periods")
    default_cycle_days: int = Field(30, description="Default billing cycle in days")
    
    # Payment properties
    allows_partial_payments: bool = Field(False, description="Can customer pay partially")
    auto_suspend_on_overdue: bool = Field(True, description="Auto-suspend when overdue")
    grace_period_days: int = Field(3, description="Grace period before suspension")
    
    # Credit properties
    supports_credit_limit: bool = Field(False, description="Does this type support credit limits")
    default_credit_limit: int = Field(0, description="Default credit limit (in cents)")
    
    # UI properties
    color_hex: str = Field("#6B7280", max_length=7, description="Color for billing type badges (#RRGGBB)")
    icon_name: Optional[str] = Field(None, max_length=50, description="Icon identifier for UI")


class BillingTypeCreate(BillingTypeBase):
    """Schema for creating billing type."""
    pass


class BillingTypeUpdate(BaseModel):
    """Schema for updating billing type."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    is_recurring: Optional[bool] = None
    requires_prepayment: Optional[bool] = None
    supports_prorating: Optional[bool] = None
    default_cycle_days: Optional[int] = None
    allows_partial_payments: Optional[bool] = None
    auto_suspend_on_overdue: Optional[bool] = None
    grace_period_days: Optional[int] = None
    supports_credit_limit: Optional[bool] = None
    default_credit_limit: Optional[int] = None
    color_hex: Optional[str] = Field(None, max_length=7)
    icon_name: Optional[str] = Field(None, max_length=50)


class BillingType(BillingTypeBase):
    """Schema for billing type response."""
    id: int
    is_system: bool = Field(..., description="System billing types cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None
