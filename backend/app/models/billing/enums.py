"""
Billing System Enumerations

All enumerations used across the enhanced billing system.
"""

from enum import Enum


# Align with existing database enums to avoid conflicts
class BillingType(str, Enum):
    """Billing account types - using simple string values"""

    PREPAID = "prepaid"
    POSTPAID = "postpaid"
    HYBRID = "hybrid"


class AccountStatus(str, Enum):
    """Customer billing account status - using simple string values"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    PENDING = "pending"


class TransactionType(str, Enum):
    """Transaction types for billing operations - using simple string values"""

    CHARGE = "charge"
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionCategory(str, Enum):
    """Categories for transaction classification - using simple string values"""

    SERVICE_FEE = "service_fee"
    SETUP_FEE = "setup_fee"
    USAGE_CHARGE = "usage_charge"
    LATE_FEE = "late_fee"
    DISCOUNT = "discount"
    TAX = "tax"
    ADJUSTMENT = "adjustment"
    PAYMENT = "payment"
    REFUND = "refund"


# Use existing database enum names to avoid conflicts
class InvoiceStatus(str, Enum):
    """Invoice status values - matches existing 'invoicestatus' enum"""

    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status values - matches existing 'paymentstatus' enum"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethodType(str, Enum):
    """Payment method types - matches existing 'paymentmethod' enum where possible"""

    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_MONEY = "mobile_money"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"
    CRYPTOCURRENCY = "cryptocurrency"
    CRYPTO = "crypto"
    OTHER = "other"


class DunningStatus(str, Enum):
    """Dunning status enumeration"""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentPlanStatus(str, Enum):
    """Payment plan status enumeration"""

    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class BillingCycleType(str, Enum):
    """Billing cycle type enumeration"""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class CreditNoteReason(str, Enum):
    """Credit note reason enumeration"""

    SERVICE_CREDIT = "service_credit"
    BILLING_ERROR = "billing_error"
    SERVICE_DOWNTIME = "service_downtime"
    CUSTOMER_COMPLAINT = "customer_complaint"
    PROMOTIONAL_CREDIT = "promotional_credit"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    OTHER = "other"


class InstallmentStatus(str, Enum):
    """Payment plan installment status"""

    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    DEFAULTED = "defaulted"


class DunningActionType(str, Enum):
    """Dunning action types"""

    EMAIL_REMINDER = "email_reminder"
    SMS_REMINDER = "sms_reminder"
    PHONE_CALL = "phone_call"
    LETTER = "letter"
    ACCOUNT_SUSPENSION = "account_suspension"
    SERVICE_RESTRICTION = "service_restriction"
    COLLECTION_AGENCY = "collection_agency"
    LEGAL_ACTION = "legal_action"


class EscalationLevel(str, Enum):
    """Dunning escalation levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryStatus(str, Enum):
    """Message delivery status"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
