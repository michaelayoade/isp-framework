from pydantic import BaseModel
from pydantic import EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .customer_status import CustomerStatus  # Import CustomerStatus schema


class CustomerBase(BaseModel):
    """Base customer schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: Optional[EmailStr] = Field(None, description="Customer email address")
    phone: Optional[str] = Field(None, max_length=50, description="Customer phone number")
    category: str = Field("person", description="Customer category: person or company")
    
    # Address fields
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP/Postal code")
    
    # Extended fields
    billing_email: Optional[EmailStr] = Field(None, description="Billing email address")
    gps: Optional[str] = Field(None, max_length=100, description="GPS coordinates (latitude,longitude)")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom metadata fields")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    password: Optional[str] = Field(None, min_length=6, description="Customer password")
    status_id: Optional[int] = Field(None, description="Customer status ID")


class CustomerUpdate(BaseModel):
    """Schema for updating an existing customer."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    status_id: Optional[int] = Field(None, description="Customer status ID")
    category: Optional[str] = Field(None, description="Customer category")
    
    # Address fields
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    
    # Extended fields
    billing_email: Optional[EmailStr] = Field(None, description="Billing email address")
    gps: Optional[str] = Field(None, max_length=100, description="GPS coordinates (latitude,longitude)")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom metadata fields")


class Customer(CustomerBase):
    """Schema for customer response."""
    id: int
    portal_id: str = Field(..., description="Portal ID for RADIUS/portal/PPPoE authentication")
    status_id: int
    status_ref: Optional[CustomerStatus] = Field(None, description="Customer status details")
    created_at: datetime
    updated_at: Optional[datetime] = None
    

class CustomerSummary(BaseModel):
    """Simplified customer schema for lists."""
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    status_id: int
    status_ref: Optional[CustomerStatus] = Field(None, description="Customer status details")
    category: str
    created_at: datetime
    

class CustomerList(BaseModel):
    """Schema for paginated customer list response."""
    customers: List[CustomerSummary]
    total: int = Field(..., description="Total number of customers")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


class CustomerStatusUpdate(BaseModel):
    """Schema for updating customer status."""
    status: str = Field(..., description="New customer status")


# Contact Type Schemas
class ContactTypeBase(BaseModel):
    """Base schema for contact types."""
    code: str = Field(..., min_length=1, max_length=50, description="Contact type code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, max_length=255, description="Optional description")
    is_active: bool = Field(True, description="Is contact type active")
    sort_order: int = Field(0, description="Sort order for UI")


class ContactTypeCreate(ContactTypeBase):
    """Schema for creating contact type."""
    pass


class ContactTypeUpdate(BaseModel):
    """Schema for updating contact type."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ContactType(ContactTypeBase):
    """Schema for contact type response."""
    id: int
    is_system: bool = Field(..., description="System types cannot be deleted")
    created_at: datetime
    updated_at: Optional[datetime] = None


# Extended Customer Information Schemas
class CustomerContactBase(BaseModel):
    """Base schema for customer contacts."""
    contact_type_id: int = Field(..., description="Contact type ID")
    name: str = Field(..., min_length=1, max_length=255, description="Contact name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    mobile: Optional[str] = Field(None, max_length=50, description="Contact mobile")
    position: Optional[str] = Field(None, max_length=100, description="Job title/position")
    is_primary: bool = Field(False, description="Is primary contact")
    receive_notifications: bool = Field(True, description="Receive notifications")
    receive_billing: bool = Field(False, description="Receive billing notifications")
    receive_technical: bool = Field(False, description="Receive technical notifications")


class CustomerContactCreate(CustomerContactBase):
    """Schema for creating customer contact."""
    pass


class CustomerContactUpdate(BaseModel):
    """Schema for updating customer contact."""
    contact_type_id: Optional[int] = Field(None, description="Contact type ID")
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None
    receive_notifications: Optional[bool] = None
    receive_billing: Optional[bool] = None
    receive_technical: Optional[bool] = None


class CustomerContact(CustomerContactBase):
    """Schema for customer contact response."""
    id: int
    customer_id: int
    contact_type: ContactType = Field(..., description="Contact type information")
    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerExtendedBase(BaseModel):
    """Base schema for extended customer information."""
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    tax_number: Optional[str] = Field(None, max_length=100, description="Tax number")
    registration_number: Optional[str] = Field(None, max_length=100, description="Registration number")
    language: str = Field("en", max_length=10, description="Preferred language")
    timezone: str = Field("UTC", max_length=50, description="Timezone")
    currency: str = Field("NGN", max_length=3, description="Currency")
    email_notifications: bool = Field(True, description="Email notifications enabled")
    sms_notifications: bool = Field(False, description="SMS notifications enabled")
    marketing_emails: bool = Field(False, description="Marketing emails enabled")
    portal_theme: str = Field("default", max_length=50, description="Portal theme")
    dashboard_layout: Optional[Dict[str, Any]] = Field(None, description="Dashboard layout preferences")


class CustomerExtendedCreate(CustomerExtendedBase):
    """Schema for creating extended customer info."""
    pass


class CustomerExtendedUpdate(BaseModel):
    """Schema for updating extended customer info."""
    company_name: Optional[str] = Field(None, max_length=255)
    tax_number: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, max_length=3)
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    portal_theme: Optional[str] = Field(None, max_length=50)
    dashboard_layout: Optional[Dict[str, Any]] = None


class CustomerExtended(CustomerExtendedBase):
    """Schema for extended customer info response."""
    customer_id: int
    login: Optional[str] = Field(None, description="Portal login username")
    created_at: datetime
    updated_at: Optional[datetime] = None


class CustomerWithExtended(Customer):
    """Schema for customer with extended information."""
    extended_info: Optional[CustomerExtended] = None
    contacts: List[CustomerContact] = Field(default_factory=list, description="Customer contacts")
    
