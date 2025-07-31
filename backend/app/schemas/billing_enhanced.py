"""
Billing Pydantic Schemas

Comprehensive Pydantic schemas for the modular billing system with validation
and serialization for all billing entities and API operations.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.billing import (
    AccountStatus,
    BillingCycleType,
    BillingType,
    CreditNoteReason,
    DunningStatus,
    InvoiceStatus,
    PaymentMethodType,
    PaymentStatus,
    TransactionCategory,
    TransactionType,
)


# Base Schemas
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# Billing Account Schemas
class BillingAccountBase(BaseModel):
    """Base billing account schema"""

    account_name: Optional[str] = Field(None, max_length=255)
    billing_type: BillingType
    account_status: Optional[AccountStatus] = AccountStatus.ACTIVE
    currency: Optional[str] = Field("USD", max_length=3)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    billing_address: Optional[str] = None
    billing_contact: Optional[str] = None
    payment_terms: Optional[int] = Field(None, ge=1, le=365)
    auto_pay_enabled: Optional[bool] = False
    additional_data: Optional[Dict[str, Any]] = None


class BillingAccountCreate(BillingAccountBase):
    """Schema for creating billing account"""

    customer_id: int = Field(..., gt=0)


class BillingAccountUpdate(BaseModel):
    """Schema for updating billing account"""

    account_name: Optional[str] = Field(None, max_length=255)
    account_status: Optional[AccountStatus] = None
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    billing_address: Optional[str] = None
    billing_contact: Optional[str] = None
    payment_terms: Optional[int] = Field(None, ge=1, le=365)
    auto_pay_enabled: Optional[bool] = None
    additional_data: Optional[Dict[str, Any]] = None


class BillingAccountResponse(BillingAccountBase, TimestampMixin):
    """Schema for billing account response"""

    id: int
    customer_id: int
    account_number: str
    available_balance: Optional[Decimal] = None
    reserved_balance: Optional[Decimal] = None
    last_billing_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None


# Balance and Transaction Schemas
class BalanceUpdateRequest(BaseModel):
    """Schema for balance update request"""

    amount: Decimal = Field(..., description="Amount to add/subtract from balance")
    transaction_type: TransactionType
    description: str = Field(..., max_length=500)
    reference_id: Optional[int] = None


class BalanceResponse(BaseModel):
    """Schema for balance response"""

    available_balance: Decimal
    reserved_balance: Decimal
    total_balance: Decimal
    credit_limit: Decimal


class TransactionResponse(TimestampMixin):
    """Schema for transaction response"""

    id: int
    transaction_id: str
    billing_account_id: int
    transaction_type: TransactionType
    transaction_category: TransactionCategory
    amount: Decimal
    currency: str
    description: str
    reference_id: Optional[int] = None
    effective_date: datetime
    additional_data: Optional[Dict[str, Any]] = None


# Invoice Schemas
class InvoiceItemCreate(BaseModel):
    """Schema for creating invoice item"""

    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    service_period_start: Optional[datetime] = None
    service_period_end: Optional[datetime] = None
    additional_data: Optional[Dict[str, Any]] = None


class InvoiceItemResponse(InvoiceItemCreate, TimestampMixin):
    """Schema for invoice item response"""

    id: int
    invoice_id: int
    proration_factor: Optional[Decimal] = None


class InvoiceBase(BaseModel):
    """Base invoice schema"""

    description: Optional[str] = Field(None, max_length=1000)
    due_date: datetime
    currency: Optional[str] = Field("USD", max_length=3)
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class InvoiceCreate(InvoiceBase):
    """Schema for creating invoice"""

    billing_account_id: int = Field(..., gt=0)
    invoice_items: List[InvoiceItemCreate] = Field(..., min_items=1)


class InvoiceUpdate(BaseModel):
    """Schema for updating invoice"""

    description: Optional[str] = Field(None, max_length=1000)
    due_date: Optional[datetime] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    """Schema for invoice response"""

    id: int
    invoice_number: str
    billing_account_id: int
    invoice_status: InvoiceStatus
    invoice_date: datetime
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    sent_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    invoice_items: Optional[List[InvoiceItemResponse]] = None


# Payment Schemas
class PaymentMethodCreate(BaseModel):
    """Schema for creating payment method"""

    billing_account_id: int = Field(..., gt=0)
    method_type: PaymentMethodType
    method_name: Optional[str] = Field(None, max_length=255)
    is_default: Optional[bool] = False
    card_last_four: Optional[str] = Field(None, max_length=4)
    card_expiry: Optional[str] = Field(None, max_length=7)  # MM/YYYY
    bank_account_last_four: Optional[str] = Field(None, max_length=4)
    gateway_customer_id: Optional[str] = None
    gateway_payment_method_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class PaymentMethodResponse(PaymentMethodCreate, TimestampMixin):
    """Schema for payment method response"""

    id: int
    is_active: bool


class PaymentCreate(BaseModel):
    """Schema for creating payment"""

    billing_account_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    payment_method_id: int = Field(..., gt=0)
    invoice_id: Optional[int] = None
    currency: Optional[str] = Field("USD", max_length=3)
    description: Optional[str] = Field(None, max_length=500)
    gateway_transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None


class PaymentResponse(PaymentCreate, TimestampMixin):
    """Schema for payment response"""

    id: int
    payment_reference: str
    payment_status: PaymentStatus
    payment_date: datetime
    processed_date: Optional[datetime] = None
    failure_reason: Optional[str] = None


# Credit Note Schemas
class CreditNoteCreate(BaseModel):
    """Schema for creating credit note"""

    billing_account_id: int = Field(..., gt=0)
    original_invoice_id: Optional[int] = None
    credit_amount: Decimal = Field(..., gt=0)
    currency: Optional[str] = Field("USD", max_length=3)
    reason: CreditNoteReason
    description: str = Field(..., max_length=1000)
    credit_date: Optional[datetime] = None
    additional_data: Optional[Dict[str, Any]] = None


class CreditNoteResponse(CreditNoteCreate, TimestampMixin):
    """Schema for credit note response"""

    id: int
    credit_number: str
    is_applied: bool
    applied_date: Optional[datetime] = None


# Payment Plan Schemas
class PaymentPlanCreate(BaseModel):
    """Schema for creating payment plan"""

    billing_account_id: int = Field(..., gt=0)
    original_amount: Decimal = Field(..., gt=0)
    plan_name: str = Field(..., max_length=255)
    number_of_installments: int = Field(..., ge=2, le=60)
    installment_amount: Decimal = Field(..., gt=0)
    first_installment_date: datetime
    installment_frequency: str = Field("monthly", max_length=50)
    setup_fee: Optional[Decimal] = Field(None, ge=0)
    interest_rate: Optional[Decimal] = Field(None, ge=0, le=1)
    additional_data: Optional[Dict[str, Any]] = None


class PaymentPlanResponse(PaymentPlanCreate, TimestampMixin):
    """Schema for payment plan response"""

    id: int
    is_active: bool
    remaining_balance: Decimal
    paid_installments: int
    next_installment_date: Optional[datetime] = None


# Dunning Schemas
class DunningCaseCreate(BaseModel):
    """Schema for creating dunning case"""

    billing_account_id: int = Field(..., gt=0)
    overdue_amount: Decimal = Field(..., gt=0)
    days_overdue: int = Field(..., ge=0)
    dunning_level: int = Field(..., ge=1, le=5)
    next_action_date: datetime
    description: Optional[str] = Field(None, max_length=1000)
    additional_data: Optional[Dict[str, Any]] = None


class DunningCaseResponse(DunningCaseCreate, TimestampMixin):
    """Schema for dunning case response"""

    id: int
    case_number: str
    dunning_status: DunningStatus
    is_active: bool
    last_action_date: Optional[datetime] = None
    resolution_date: Optional[datetime] = None


# Billing Cycle Schemas
class BillingCycleCreate(BaseModel):
    """Schema for creating billing cycle"""

    billing_account_id: int = Field(..., gt=0)
    cycle_name: str = Field(..., max_length=255)
    cycle_type: BillingCycleType
    cycle_start_date: datetime
    cycle_end_date: datetime
    billing_date: datetime
    due_date: datetime
    is_prorated: Optional[bool] = False
    additional_data: Optional[Dict[str, Any]] = None


class BillingCycleResponse(BillingCycleCreate, TimestampMixin):
    """Schema for billing cycle response"""

    id: int
    is_processed: bool
    processed_date: Optional[datetime] = None
    total_amount: Optional[Decimal] = None
    invoice_count: Optional[int] = None


# Report and Analytics Schemas
class AccountSummaryResponse(BaseModel):
    """Schema for account summary response"""

    account_info: Dict[str, Any]
    transaction_summary: Dict[str, Any]
    invoice_summary: Dict[str, Any]
    payment_summary: Dict[str, Any]


class BillingReportResponse(BaseModel):
    """Schema for billing report response"""

    report_date: datetime
    total_accounts: int
    active_accounts: int
    pending_invoices: int
    overdue_invoices: int
    completed_payments: int
    failed_payments: int
    billing_type_filter: Optional[BillingType] = None
    date_range: Optional[Dict[str, Optional[datetime]]] = None


# Search and Filter Schemas
class BillingAccountSearchRequest(BaseModel):
    """Schema for billing account search request"""

    search_term: Optional[str] = None
    billing_type: Optional[BillingType] = None
    account_status: Optional[AccountStatus] = None
    min_balance: Optional[Decimal] = None
    max_balance: Optional[Decimal] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class InvoiceSearchRequest(BaseModel):
    """Schema for invoice search request"""

    search_term: Optional[str] = None
    account_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class PaymentSearchRequest(BaseModel):
    """Schema for payment search request"""

    search_term: Optional[str] = None
    account_id: Optional[int] = None
    status: Optional[PaymentStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# Pagination Schemas
class PaginatedResponse(BaseModel):
    """Generic paginated response schema"""

    items: List[Any]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool

    @field_validator("has_next", always=True)
    def validate_has_next(cls, v, values):
        total = values.get("total", 0)
        limit = values.get("limit", 0)
        offset = values.get("offset", 0)
        return (offset + limit) < total

    @field_validator("has_previous", always=True)
    def validate_has_previous(cls, v, values):
        offset = values.get("offset", 0)
        return offset > 0


class PaginatedBillingAccountResponse(PaginatedResponse):
    """Paginated billing account response"""

    items: List[BillingAccountResponse]


class PaginatedInvoiceResponse(PaginatedResponse):
    """Paginated invoice response"""

    items: List[InvoiceResponse]


class PaginatedPaymentResponse(PaginatedResponse):
    """Paginated payment response"""

    items: List[PaymentResponse]


class PaginatedTransactionResponse(PaginatedResponse):
    """Paginated transaction response"""

    items: List[TransactionResponse]


# Validation Schemas
class BillingValidationResponse(BaseModel):
    """Schema for billing validation response"""

    is_valid: bool
    validation_errors: List[str] = []
    warnings: List[str] = []


class BalanceValidationRequest(BaseModel):
    """Schema for balance validation request"""

    account_id: int = Field(..., gt=0)
    requested_amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType


class BalanceValidationResponse(BillingValidationResponse):
    """Schema for balance validation response"""

    available_balance: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    can_process: bool


# Bulk Operation Schemas
class BulkInvoiceCreate(BaseModel):
    """Schema for bulk invoice creation"""

    billing_account_ids: List[int] = Field(..., min_items=1)
    invoice_template: InvoiceBase
    invoice_items_template: List[InvoiceItemCreate]


class BulkPaymentProcess(BaseModel):
    """Schema for bulk payment processing"""

    payment_requests: List[PaymentCreate] = Field(..., min_items=1)


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response"""

    total_requested: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []
    results: List[Dict[str, Any]] = []


# Configuration Schemas
class BillingConfigurationResponse(BaseModel):
    """Schema for billing configuration response"""

    supported_currencies: List[str]
    default_currency: str
    supported_payment_methods: List[PaymentMethodType]
    default_payment_terms: int
    max_credit_limit: Decimal
    dunning_levels: List[Dict[str, Any]]
    billing_cycle_types: List[BillingCycleType]
