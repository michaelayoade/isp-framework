from pydantic import BaseModel
from pydantic import  Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


class CustomerContactCreate(BaseModel):
    """Schema for creating customer contact"""
    contact_type: str = Field("primary", description="Contact type")
    name: str = Field(..., description="Contact name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    mobile: Optional[str] = Field(None, description="Contact mobile")
    address_line_1: Optional[str] = Field(None, description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state_province: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(None, description="Country")
    position: Optional[str] = Field(None, description="Position/Title")
    department: Optional[str] = Field(None, description="Department")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_primary: bool = Field(False, description="Is primary contact")


class CustomerContactResponse(BaseModel):
    """Schema for customer contact response"""
    id: int
    customer_id: int
    contact_type: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state_province: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]
    position: Optional[str]
    department: Optional[str]
    notes: Optional[str]
    is_active: bool
    is_primary: bool
    created_at: datetime
    updated_at: Optional[datetime]


class CustomerLabelCreate(BaseModel):
    """Schema for creating customer label"""
    name: str = Field(..., description="Label name")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Label description")
    color: str = Field("#007bff", description="Label color (hex)")
    category: Optional[str] = Field(None, description="Label category")
    priority: int = Field(0, description="Label priority")


class CustomerLabelResponse(BaseModel):
    """Schema for customer label response"""
    id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    color: str
    category: Optional[str]
    priority: int
    is_active: bool
    is_system: bool
    partner_id: int
    created_at: datetime
    updated_at: Optional[datetime]


class CustomerNoteCreate(BaseModel):
    """Schema for creating customer note"""
    title: Optional[str] = Field(None, description="Note title")
    content: str = Field(..., description="Note content")
    note_type: str = Field("general", description="Note type")
    is_internal: bool = Field(True, description="Is internal note")
    priority: str = Field("normal", description="Note priority")


class CustomerNoteResponse(BaseModel):
    """Schema for customer note response"""
    id: int
    customer_id: int
    title: Optional[str]
    content: str
    note_type: str
    is_internal: bool
    priority: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]


class CustomerDocumentCreate(BaseModel):
    """Schema for creating customer document"""
    document_name: str = Field(..., description="Document name")
    document_type: Optional[str] = Field(None, description="Document type")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    description: Optional[str] = Field(None, description="Document description")
    document_date: Optional[date] = Field(None, description="Document date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")


class CustomerDocumentResponse(BaseModel):
    """Schema for customer document response"""
    id: int
    customer_id: int
    document_name: str
    document_type: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    description: Optional[str]
    document_date: Optional[date]
    expiry_date: Optional[date]
    status: str
    is_verified: bool
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    uploaded_by: int
    created_at: datetime
    updated_at: Optional[datetime]


class CustomerBillingConfigCreate(BaseModel):
    """Schema for creating customer billing configuration"""
    billing_cycle: str = Field("monthly", description="Billing cycle")
    billing_day: int = Field(1, description="Billing day")
    invoice_template: Optional[str] = Field(None, description="Invoice template")
    payment_terms: int = Field(30, description="Payment terms in days")
    late_fee_percentage: Decimal = Field(Decimal("0.00"), description="Late fee percentage")
    grace_period_days: int = Field(7, description="Grace period in days")
    credit_limit: Decimal = Field(Decimal("0.00"), description="Credit limit")
    credit_check_required: bool = Field(False, description="Credit check required")
    auto_suspend_on_overdue: bool = Field(True, description="Auto suspend on overdue")
    default_discount_percentage: Decimal = Field(Decimal("0.00"), description="Default discount percentage")
    loyalty_discount_eligible: bool = Field(True, description="Loyalty discount eligible")
    tax_exempt: bool = Field(False, description="Tax exempt")
    tax_id: Optional[str] = Field(None, description="Tax ID")
    tax_rate_override: Optional[Decimal] = Field(None, description="Tax rate override")


class CustomerBillingConfigResponse(BaseModel):
    """Schema for customer billing configuration response"""
    id: int
    customer_id: int
    billing_cycle: str
    billing_day: int
    invoice_template: Optional[str]
    payment_terms: int
    late_fee_percentage: Decimal
    grace_period_days: int
    credit_limit: Decimal
    credit_check_required: bool
    auto_suspend_on_overdue: bool
    default_discount_percentage: Decimal
    loyalty_discount_eligible: bool
    tax_exempt: bool
    tax_id: Optional[str]
    tax_rate_override: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]


class CustomerExtendedCreate(BaseModel):
    """Schema for creating extended customer"""
    login: Optional[str] = Field(None, description="Customer login")
    password: Optional[str] = Field(None, description="Customer password")
    name: str = Field(..., description="Customer name")
    email: EmailStr = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    category: str = Field("person", description="Customer category")
    
    # Address Information
    address_line_1: Optional[str] = Field(None, description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state_province: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: str = Field("Nigeria", description="Country")
    
    # Billing Configuration
    billing_type: str = Field("postpaid", description="Billing type")
    billing_day: int = Field(1, description="Billing day")
    payment_method: Optional[str] = Field(None, description="Payment method")
    credit_limit: Decimal = Field(Decimal("0.00"), description="Credit limit")
    
    # Hierarchical Structure
    parent_customer_id: Optional[int] = Field(None, description="Parent customer ID")
    
    # Partner/Location Assignment
    partner_id: int = Field(1, description="Partner ID")
    location_id: int = Field(1, description="Location ID")
    
    # Additional Information
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    occupation: Optional[str] = Field(None, description="Occupation")
    company_registration: Optional[str] = Field(None, description="Company registration")
    tax_id: Optional[str] = Field(None, description="Tax ID")
    
    # Communication Preferences
    preferred_language: str = Field("en", description="Preferred language")
    communication_method: str = Field("email", description="Communication method")
    marketing_consent: bool = Field(False, description="Marketing consent")
    
    # Account Settings
    auto_payment: bool = Field(False, description="Auto payment enabled")
    invoice_delivery: str = Field("email", description="Invoice delivery method")
    notification_preferences: Dict[str, Any] = Field(default_factory=dict, description="Notification preferences")
    
    # Custom Fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom fields")
    
    # Tags and Labels
    tags: Optional[str] = Field(None, description="Customer tags")

    @field_validator('billing_day')
    def validate_billing_day(cls, v):
        if not 1 <= v <= 31:
            raise ValueError('Billing day must be between 1 and 31')
        return v


class CustomerExtendedUpdate(BaseModel):
    """Schema for updating extended customer"""
    name: Optional[str] = Field(None, description="Customer name")
    email: Optional[EmailStr] = Field(None, description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone")
    status: Optional[str] = Field(None, description="Customer status")
    category: Optional[str] = Field(None, description="Customer category")
    
    # Address Information
    address_line_1: Optional[str] = Field(None, description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state_province: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(None, description="Country")
    
    # Billing Configuration
    billing_type: Optional[str] = Field(None, description="Billing type")
    billing_day: Optional[int] = Field(None, description="Billing day")
    payment_method: Optional[str] = Field(None, description="Payment method")
    credit_limit: Optional[Decimal] = Field(None, description="Credit limit")
    
    # Additional Information
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    occupation: Optional[str] = Field(None, description="Occupation")
    company_registration: Optional[str] = Field(None, description="Company registration")
    tax_id: Optional[str] = Field(None, description="Tax ID")
    
    # Communication Preferences
    preferred_language: Optional[str] = Field(None, description="Preferred language")
    communication_method: Optional[str] = Field(None, description="Communication method")
    marketing_consent: Optional[bool] = Field(None, description="Marketing consent")
    
    # Account Settings
    auto_payment: Optional[bool] = Field(None, description="Auto payment enabled")
    invoice_delivery: Optional[str] = Field(None, description="Invoice delivery method")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification preferences")
    
    # Custom Fields
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="Custom fields")
    
    # Tags
    tags: Optional[str] = Field(None, description="Customer tags")


class CustomerExtendedResponse(BaseModel):
    """Schema for extended customer response"""
    id: int
    login: str
    name: str
    email: str
    phone: Optional[str]
    status: str
    category: str
    
    # Address Information
    address_line_1: Optional[str]
    address_line_2: Optional[str]
    city: Optional[str]
    state_province: Optional[str]
    postal_code: Optional[str]
    country: str
    
    # Billing Configuration
    billing_type: str
    billing_day: int
    payment_method: Optional[str]
    credit_limit: Decimal
    current_balance: Decimal
    
    # Hierarchical Structure
    parent_customer_id: Optional[int]
    is_main_account: bool
    account_level: int
    
    # Partner/Location Assignment
    partner_id: int
    location_id: int
    
    # Additional Information
    date_of_birth: Optional[date]
    gender: Optional[str]
    occupation: Optional[str]
    company_registration: Optional[str]
    tax_id: Optional[str]
    
    # Communication Preferences
    preferred_language: str
    communication_method: str
    marketing_consent: bool
    
    # Account Settings
    auto_payment: bool
    invoice_delivery: str
    notification_preferences: Dict[str, Any]
    
    # Custom Fields
    custom_fields: Dict[str, Any]
    
    # Tags and Labels
    tags: Optional[str]
    labels: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]


class CustomerDetailsResponse(BaseModel):
    """Schema for comprehensive customer details"""
    customer: CustomerExtendedResponse
    contacts: List[CustomerContactResponse]
    labels: List[CustomerLabelResponse]
    notes: List[CustomerNoteResponse]
    documents: List[CustomerDocumentResponse]
    billing_config: Optional[CustomerBillingConfigResponse]
    child_customers: List[CustomerExtendedResponse]
    account_summary: Dict[str, Any]


class CustomerSearchRequest(BaseModel):
    """Schema for customer search request"""
    query: Optional[str] = Field(None, description="Search query")
    status: Optional[str] = Field(None, description="Customer status filter")
    category: Optional[str] = Field(None, description="Customer category filter")
    labels: Optional[List[str]] = Field(None, description="Label filters")
    location_id: Optional[int] = Field(None, description="Location filter")
    partner_id: Optional[int] = Field(None, description="Partner filter")
    limit: int = Field(50, description="Results limit", ge=1, le=100)
    offset: int = Field(0, description="Results offset", ge=0)


class CustomerSearchResponse(BaseModel):
    """Schema for customer search response"""
    customers: List[CustomerExtendedResponse]
    total_count: int
    limit: int
    offset: int


class CustomerStatusChangeRequest(BaseModel):
    """Schema for customer status change"""
    new_status: str = Field(..., description="New customer status")
    reason: Optional[str] = Field(None, description="Reason for status change")


class CustomerLabelAssignmentRequest(BaseModel):
    """Schema for customer label assignment"""
    label_id: int = Field(..., description="Label ID to assign")
    notes: Optional[str] = Field(None, description="Assignment notes")


class CustomerHierarchyResponse(BaseModel):
    """Schema for customer hierarchy response"""
    customer: CustomerExtendedResponse
    parent_chain: List[CustomerExtendedResponse]
    descendants: List[Dict[str, Any]]
    total_descendants: int
