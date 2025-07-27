from ._base import BaseSchema
from pydantic import  EmailStr, Field
from typing import Optional, List
from datetime import datetime


class CustomerBase(BaseSchema):
    """Base customer schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    email: Optional[EmailStr] = Field(None, description="Customer email address")
    phone: Optional[str] = Field(None, max_length=50, description="Customer phone number")
    category: str = Field("person", description="Customer category: person or company")
    
    # Address fields
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP/Postal code")


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer."""
    password: Optional[str] = Field(None, min_length=6, description="Customer password")


class CustomerUpdate(BaseSchema):
    """Schema for updating an existing customer."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, description="Customer status")
    category: Optional[str] = Field(None, description="Customer category")
    
    # Address fields
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)


class Customer(CustomerBase):
    """Schema for customer response."""
    id: int
    portal_id: str = Field(..., description="Portal ID for RADIUS/portal/PPPoE authentication")
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    

class CustomerSummary(BaseSchema):
    """Simplified customer schema for lists."""
    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    status: str
    category: str
    created_at: datetime
    

class CustomerList(BaseSchema):
    """Schema for paginated customer list response."""
    customers: List[CustomerSummary]
    total: int = Field(..., description="Total number of customers")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


class CustomerStatusUpdate(BaseSchema):
    """Schema for updating customer status."""
    status: str = Field(..., description="New customer status")
    
