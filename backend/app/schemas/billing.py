"""
Billing System Schemas

Comprehensive Pydantic schemas for billing module including invoices, payments,
credit notes, and accounting for ISP Framework.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class InvoiceStatus(str, Enum):
    """Invoice status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    CHECK = "check"
    OTHER = "other"


class CreditNoteReason(str, Enum):
    """Credit note reason enumeration"""
    REFUND = "refund"
    DISCOUNT = "discount"
    ERROR_CORRECTION = "error_correction"
    SERVICE_CREDIT = "service_credit"
    GOODWILL = "goodwill"
    OTHER = "other"


# Invoice Schemas
class InvoiceItemBase(BaseModel):
    """Base schema for invoice items"""
    description: str = Field(..., min_length=1, max_length=500)
    item_type: Optional[str] = Field(None, max_length=50)
    service_id: Optional[int] = Field(None, gt=0)
    product_id: Optional[int] = Field(None, gt=0)
    quantity: Decimal = Field(1, gt=0)
    unit_price: Decimal = Field(...)
    discount_percentage: Decimal = Field(0, ge=0, le=100)
    discount_amount: Decimal = Field(0, ge=0)
    taxable: bool = True
    tax_rate: Decimal = Field(0, ge=0, le=100)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    additional_data: Optional[dict] = None


class InvoiceItemCreate(InvoiceItemBase):
    """Schema for creating invoice items"""
    pass


class InvoiceItemUpdate(BaseModel):
    """Schema for updating invoice items"""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    item_type: Optional[str] = Field(None, max_length=50)
    service_id: Optional[int] = Field(None, gt=0)
    product_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    taxable: Optional[bool] = None
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    additional_data: Optional[dict] = None


class InvoiceItemResponse(InvoiceItemBase):
    """Schema for invoice item responses"""
    id: int
    invoice_id: int
    line_total: Decimal
    tax_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]


class InvoiceBase(BaseModel):
    """Base schema for invoices"""
    customer_id: int = Field(..., gt=0)
    invoice_date: datetime
    due_date: datetime
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    currency: str = Field("USD", min_length=3, max_length=3)
    tax_rate: Decimal = Field(0, ge=0, le=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    template_id: Optional[int] = Field(None, gt=0)
    billing_cycle_id: Optional[int] = Field(None, gt=0)
    parent_invoice_id: Optional[int] = Field(None, gt=0)
    additional_data: Optional[dict] = None

    @field_validator('due_date')
    @classmethod
    def due_date_must_be_after_invoice_date(cls, v, info):
        if hasattr(info, 'data') and 'invoice_date' in info.data and v <= info.data['invoice_date']:
            raise ValueError('Due date must be after invoice date')
        return v


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices"""
    items: List[InvoiceItemCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoices"""
    customer_id: Optional[int] = Field(None, gt=0)
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    billing_period_start: Optional[datetime] = None
    billing_period_end: Optional[datetime] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    description: Optional[str] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    template_id: Optional[int] = Field(None, gt=0)
    billing_cycle_id: Optional[int] = Field(None, gt=0)
    parent_invoice_id: Optional[int] = Field(None, gt=0)
    additional_data: Optional[dict] = None
    status: Optional[InvoiceStatus] = None


class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses"""
    id: int
    invoice_number: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    balance_due: Decimal
    status: InvoiceStatus
    sent_date: Optional[datetime]
    paid_date: Optional[datetime]
    cancelled_date: Optional[datetime]
    is_overdue: bool
    days_overdue: int
    created_at: datetime
    updated_at: Optional[datetime]
    items: List[InvoiceItemResponse] = Field(default_factory=list)


class InvoiceSearch(BaseModel):
    """Schema for invoice search parameters"""
    customer_id: Optional[int] = Field(None, gt=0)
    status: Optional[InvoiceStatus] = None
    invoice_number: Optional[str] = Field(None, max_length=50)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    due_date_from: Optional[date] = None
    due_date_to: Optional[date] = None
    amount_min: Optional[Decimal] = Field(None, ge=0)
    amount_max: Optional[Decimal] = Field(None, ge=0)
    overdue_only: bool = False
    unpaid_only: bool = False


# Payment Schemas
class PaymentBase(BaseModel):
    """Base schema for payments"""
    invoice_id: int = Field(..., gt=0)
    customer_id: int = Field(..., gt=0)
    payment_date: datetime
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    payment_method: PaymentMethod
    payment_reference: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    processing_fee: Decimal = Field(0, ge=0)
    additional_data: Optional[dict] = None


class PaymentCreate(PaymentBase):
    """Schema for creating payments"""
    pass


class PaymentUpdate(BaseModel):
    """Schema for updating payments"""
    payment_date: Optional[datetime] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    payment_method: Optional[PaymentMethod] = None
    payment_reference: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=100)
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None
    processing_fee: Optional[Decimal] = Field(None, ge=0)
    additional_data: Optional[dict] = None


class PaymentResponse(PaymentBase):
    """Schema for payment responses"""
    id: int
    payment_number: str
    status: PaymentStatus
    processed_date: Optional[datetime]
    net_amount: Optional[Decimal]
    receipt_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class PaymentSearch(BaseModel):
    """Schema for payment search parameters"""
    customer_id: Optional[int] = Field(None, gt=0)
    invoice_id: Optional[int] = Field(None, gt=0)
    status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    payment_number: Optional[str] = Field(None, max_length=50)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = Field(None, ge=0)
    amount_max: Optional[Decimal] = Field(None, ge=0)


# Payment Refund Schemas
class PaymentRefundBase(BaseModel):
    """Base schema for payment refunds"""
    payment_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    reason: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class PaymentRefundCreate(PaymentRefundBase):
    """Schema for creating payment refunds"""
    refund_date: datetime


class PaymentRefundUpdate(BaseModel):
    """Schema for updating payment refunds"""
    amount: Optional[Decimal] = Field(None, gt=0)
    reason: Optional[str] = Field(None, max_length=200)
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None


class PaymentRefundResponse(PaymentRefundBase):
    """Schema for payment refund responses"""
    id: int
    refund_number: str
    refund_date: datetime
    status: PaymentStatus
    processed_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


# Credit Note Schemas
class CreditNoteBase(BaseModel):
    """Base schema for credit notes"""
    invoice_id: int = Field(..., gt=0)
    customer_id: int = Field(..., gt=0)
    credit_date: datetime
    amount: Decimal = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    reason: CreditNoteReason
    description: str = Field(..., min_length=1)
    notes: Optional[str] = None
    additional_data: Optional[dict] = None


class CreditNoteCreate(CreditNoteBase):
    """Schema for creating credit notes"""
    pass


class CreditNoteUpdate(BaseModel):
    """Schema for updating credit notes"""
    credit_date: Optional[datetime] = None
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    reason: Optional[CreditNoteReason] = None
    description: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None
    status: Optional[str] = None
    additional_data: Optional[dict] = None


class CreditNoteResponse(CreditNoteBase):
    """Schema for credit note responses"""
    id: int
    credit_note_number: str
    status: str
    applied_date: Optional[datetime]
    approved_by: Optional[int]
    approved_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]


class CreditNoteSearch(BaseModel):
    """Schema for credit note search parameters"""
    customer_id: Optional[int] = Field(None, gt=0)
    invoice_id: Optional[int] = Field(None, gt=0)
    reason: Optional[CreditNoteReason] = None
    status: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[Decimal] = Field(None, ge=0)
    amount_max: Optional[Decimal] = Field(None, ge=0)


# Billing Cycle Schemas
class BillingCycleBase(BaseModel):
    """Base schema for billing cycles"""
    cycle_name: str = Field(..., min_length=1, max_length=100)
    cycle_type: str = Field(..., pattern="^(monthly|quarterly|yearly)$")
    cycle_day: int = Field(..., ge=1, le=31)
    start_date: datetime
    end_date: datetime
    due_date: datetime
    additional_data: Optional[dict] = None

    @field_validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if (info and hasattr(info, 'data') and 'start_date' in info.data) and v <= (info.data.get('start_date') if info and hasattr(info, 'data') else None):
            raise ValueError('End date must be after start date')
        return v


class BillingCycleCreate(BillingCycleBase):
    """Schema for creating billing cycles"""
    pass


class BillingCycleUpdate(BaseModel):
    """Schema for updating billing cycles"""
    cycle_name: Optional[str] = Field(None, min_length=1, max_length=100)
    cycle_type: Optional[str] = Field(None, pattern="^(monthly|quarterly|yearly)$")
    cycle_day: Optional[int] = Field(None, ge=1, le=31)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    additional_data: Optional[dict] = None


class BillingCycleResponse(BillingCycleBase):
    """Schema for billing cycle responses"""
    id: int
    status: str
    invoices_generated: bool
    generation_date: Optional[datetime]
    total_customers: int
    total_invoices: int
    total_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]


# Accounting Schemas
class AccountingEntryBase(BaseModel):
    """Base schema for accounting entries"""
    entry_date: datetime
    description: str = Field(..., min_length=1, max_length=500)
    account_code: str = Field(..., min_length=1, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=100)
    debit_amount: Decimal = Field(0, ge=0)
    credit_amount: Decimal = Field(0, ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    invoice_id: Optional[int] = Field(None, gt=0)
    payment_id: Optional[int] = Field(None, gt=0)
    credit_note_id: Optional[int] = Field(None, gt=0)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    additional_data: Optional[dict] = None

    @field_validator('credit_amount')
    def debit_or_credit_must_be_positive(cls, v, values):
        if (info and hasattr(info, 'data') and 'debit_amount' in info.data) and (info.data.get('debit_amount') if info and hasattr(info, 'data') else None) == 0 and v == 0:
            raise ValueError('Either debit_amount or credit_amount must be greater than 0')
        return v


class AccountingEntryCreate(AccountingEntryBase):
    """Schema for creating accounting entries"""
    pass


class AccountingEntryUpdate(BaseModel):
    """Schema for updating accounting entries"""
    entry_date: Optional[datetime] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    account_code: Optional[str] = Field(None, min_length=1, max_length=20)
    account_name: Optional[str] = Field(None, min_length=1, max_length=100)
    debit_amount: Optional[Decimal] = Field(None, ge=0)
    credit_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    additional_data: Optional[dict] = None


class AccountingEntryResponse(AccountingEntryBase):
    """Schema for accounting entry responses"""
    id: int
    entry_number: str
    created_at: datetime
    updated_at: Optional[datetime]


# Tax Rate Schemas
class TaxRateBase(BaseModel):
    """Base schema for tax rates"""
    name: str = Field(..., min_length=1, max_length=100)
    rate: Decimal = Field(..., ge=0, le=100)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    state_province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    effective_date: datetime
    expiry_date: Optional[datetime] = None
    tax_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None

    @field_validator('expiry_date')
    def expiry_date_must_be_after_effective_date(cls, v, values):
        if v and (info and hasattr(info, 'data') and 'effective_date' in info.data) and v <= (info.data.get('effective_date') if info and hasattr(info, 'data') else None):
            raise ValueError('Expiry date must be after effective date')
        return v


class TaxRateCreate(TaxRateBase):
    """Schema for creating tax rates"""
    pass


class TaxRateUpdate(BaseModel):
    """Schema for updating tax rates"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate: Optional[Decimal] = Field(None, ge=0, le=100)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    state_province: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    tax_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class TaxRateResponse(TaxRateBase):
    """Schema for tax rate responses"""
    id: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime]


# Summary and Statistics Schemas
class BillingOverview(BaseModel):
    """Schema for billing overview statistics"""
    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    overdue_amount: Decimal
    draft_invoices: int
    pending_invoices: int
    paid_invoices: int
    overdue_invoices: int
    total_payments: int
    total_credit_notes: int
    average_payment_time: Optional[float]  # Days
    collection_rate: Optional[float]  # Percentage


class CustomerBillingSummary(BaseModel):
    """Schema for customer billing summary"""
    customer_id: int
    total_invoices: int
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    overdue_amount: Decimal
    last_invoice_date: Optional[datetime]
    last_payment_date: Optional[datetime]
    average_monthly_billing: Optional[Decimal]
    payment_history_score: Optional[int]  # 1-100 score
