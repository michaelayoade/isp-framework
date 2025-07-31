"""
Payment System

Comprehensive payment management with multiple payment methods,
gateway integration, and automated payment processing.
"""

from datetime import datetime, timezone

from sqlalchemy import DECIMAL, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .enums import PaymentMethodType, PaymentStatus


class PaymentMethod(Base):
    """Customer payment methods"""

    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Payment method details
    method_type = Column(SQLEnum(PaymentMethodType), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Card/Bank details (encrypted/masked)
    masked_number = Column(String(20))  # Last 4 digits only
    expiry_month = Column(Integer)
    expiry_year = Column(Integer)
    bank_name = Column(String(100))
    account_holder_name = Column(String(100))

    # Gateway integration
    gateway_customer_id = Column(String(100))
    gateway_payment_method_id = Column(String(100))
    gateway_name = Column(String(50))

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True))

    # Metadata
    nickname = Column(String(50))  # User-friendly name
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="payment_methods")
    payments = relationship("Payment", back_populates="payment_method")

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, type={self.method_type}, masked='{self.masked_number}')>"

    @property
    def is_expired(self):
        """Check if payment method is expired (for cards)"""
        if not self.expiry_month or not self.expiry_year:
            return False

        now = datetime.now()
        return self.expiry_year < now.year or (
            self.expiry_year == now.year and self.expiry_month < now.month
        )

    def get_display_name(self):
        """Get user-friendly display name"""
        if self.nickname:
            return self.nickname

        if self.method_type == PaymentMethodType.CREDIT_CARD:
            return f"Credit Card ending in {self.masked_number[-4:] if self.masked_number else '****'}"
        elif self.method_type == PaymentMethodType.BANK_TRANSFER:
            return (
                f"Bank Account - {self.bank_name}" if self.bank_name else "Bank Account"
            )
        else:
            return self.method_type.value.replace("_", " ").title()

    def get_method_summary(self):
        """Get payment method summary"""
        return {
            "id": self.id,
            "method_type": self.method_type.value,
            "display_name": self.get_display_name(),
            "masked_number": self.masked_number,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_expired": self.is_expired,
            "gateway_name": self.gateway_name,
        }


class Payment(Base):
    """Payment with gateway integration"""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))

    # Payment details
    payment_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # Status and processing
    status = Column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )
    processed_date = Column(DateTime(timezone=True))

    # Gateway integration
    gateway_transaction_id = Column(String(100), index=True)
    gateway_reference = Column(String(100))
    gateway_response = Column(JSONB)
    processing_fee = Column(DECIMAL(12, 2), default=0)
    net_amount = Column(DECIMAL(12, 2))

    # References
    payment_reference = Column(String(100))
    external_reference = Column(String(100))

    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_date = Column(DateTime(timezone=True))

    # Metadata
    notes = Column(Text)
    receipt_url = Column(String(500))
    failure_reason = Column(String(200))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_account = relationship("CustomerBillingAccount")
    invoice = relationship("Invoice", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")
    refunds = relationship("PaymentRefund", back_populates="payment")
    accounting_entries = relationship("AccountingEntry", back_populates="payment")

    # Indexes
    __table_args__ = (
        Index("idx_payments_account_date", "billing_account_id", "payment_date"),
        Index("idx_payments_status_date", "status", "payment_date"),
    )

    def __repr__(self):
        return f"<Payment(id={self.id}, number='{self.payment_number}', amount={self.amount})>"

    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == PaymentStatus.COMPLETED

    @property
    def is_failed(self):
        """Check if payment failed"""
        return self.status in [PaymentStatus.FAILED, PaymentStatus.CANCELLED]

    @property
    def can_retry(self):
        """Check if payment can be retried"""
        return (
            self.status == PaymentStatus.FAILED and self.retry_count < self.max_retries
        )

    def calculate_net_amount(self):
        """Calculate net amount after processing fees"""
        self.net_amount = self.amount - (self.processing_fee or 0)
        return self.net_amount

    def mark_as_completed(self, gateway_transaction_id=None, gateway_response=None):
        """Mark payment as completed"""
        self.status = PaymentStatus.COMPLETED
        self.processed_date = datetime.now(timezone.utc)
        if gateway_transaction_id:
            self.gateway_transaction_id = gateway_transaction_id
        if gateway_response:
            self.gateway_response = gateway_response
        self.calculate_net_amount()

    def mark_as_failed(self, failure_reason=None, gateway_response=None):
        """Mark payment as failed"""
        self.status = PaymentStatus.FAILED
        self.processed_date = datetime.now(timezone.utc)
        if failure_reason:
            self.failure_reason = failure_reason
        if gateway_response:
            self.gateway_response = gateway_response

        # Set next retry date if retries are available
        if self.can_retry:
            from datetime import timedelta

            self.next_retry_date = datetime.now(timezone.utc) + timedelta(hours=1)

    def get_payment_summary(self):
        """Get comprehensive payment summary"""
        return {
            "payment_number": self.payment_number,
            "status": self.status.value,
            "amount": float(self.amount),
            "net_amount": (
                float(self.net_amount) if self.net_amount else float(self.amount)
            ),
            "processing_fee": float(self.processing_fee) if self.processing_fee else 0,
            "currency": self.currency,
            "payment_date": self.payment_date.isoformat(),
            "processed_date": (
                self.processed_date.isoformat() if self.processed_date else None
            ),
            "gateway_transaction_id": self.gateway_transaction_id,
            "payment_reference": self.payment_reference,
            "is_successful": self.is_successful,
            "is_failed": self.is_failed,
            "can_retry": self.can_retry,
            "retry_count": self.retry_count,
            "failure_reason": self.failure_reason,
        }


class PaymentRefund(Base):
    """Payment refund records"""

    __tablename__ = "payment_refunds"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    refund_number = Column(String(50), unique=True, nullable=False, index=True)

    # Refund details
    refund_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    reason = Column(String(200), nullable=False)
    refund_type = Column(String(20), default="full")  # full, partial

    # Processing
    status = Column(
        SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING
    )
    processed_date = Column(DateTime(timezone=True))

    # Gateway integration
    gateway_refund_id = Column(String(100))
    gateway_response = Column(JSONB)

    # Metadata
    notes = Column(Text)
    processed_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    processor = relationship("Administrator", foreign_keys=[processed_by])

    def __repr__(self):
        return f"<PaymentRefund(id={self.id}, number='{self.refund_number}', amount={self.amount})>"

    @property
    def is_full_refund(self):
        """Check if this is a full refund"""
        return self.refund_type == "full" or self.amount >= self.payment.amount

    def get_refund_summary(self):
        """Get refund summary"""
        return {
            "refund_number": self.refund_number,
            "status": self.status.value,
            "amount": float(self.amount),
            "reason": self.reason,
            "refund_type": self.refund_type,
            "refund_date": self.refund_date.isoformat(),
            "processed_date": (
                self.processed_date.isoformat() if self.processed_date else None
            ),
            "gateway_refund_id": self.gateway_refund_id,
            "is_full_refund": self.is_full_refund,
        }


class PaymentGateway(Base):
    """Payment gateway configurations"""

    __tablename__ = "payment_gateways"

    id = Column(Integer, primary_key=True, index=True)
    gateway_name = Column(String(50), nullable=False, unique=True)
    gateway_type = Column(
        String(30), nullable=False
    )  # stripe, paypal, flutterwave, etc.

    # Configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    supports_refunds = Column(Boolean, default=True)
    supports_recurring = Column(Boolean, default=False)

    # Supported payment methods
    supported_methods = Column(JSONB)  # List of supported PaymentMethodType values

    # API Configuration (encrypted)
    api_endpoint = Column(String(200))
    api_version = Column(String(20))

    # Fees and limits
    transaction_fee_percentage = Column(DECIMAL(5, 2), default=0)
    transaction_fee_fixed = Column(DECIMAL(12, 2), default=0)
    minimum_amount = Column(DECIMAL(12, 2), default=0)
    maximum_amount = Column(DECIMAL(12, 2))

    # Metadata
    description = Column(Text)
    configuration = Column(JSONB)  # Gateway-specific settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PaymentGateway(id={self.id}, name='{self.gateway_name}', type={self.gateway_type})>"

    def calculate_fees(self, amount):
        """Calculate gateway fees for given amount"""
        percentage_fee = (
            amount * (self.transaction_fee_percentage / 100)
            if self.transaction_fee_percentage
            else 0
        )
        fixed_fee = self.transaction_fee_fixed or 0
        return percentage_fee + fixed_fee

    def is_amount_valid(self, amount):
        """Check if amount is within gateway limits"""
        if self.minimum_amount and amount < self.minimum_amount:
            return False
        if self.maximum_amount and amount > self.maximum_amount:
            return False
        return True

    def supports_payment_method(self, method_type):
        """Check if gateway supports given payment method"""
        if not self.supported_methods:
            return True  # Assume all methods supported if not specified
        return method_type.value in self.supported_methods

    def get_gateway_summary(self):
        """Get gateway configuration summary"""
        return {
            "gateway_name": self.gateway_name,
            "gateway_type": self.gateway_type,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "supports_refunds": self.supports_refunds,
            "supports_recurring": self.supports_recurring,
            "supported_methods": self.supported_methods,
            "fees": {
                "percentage": (
                    float(self.transaction_fee_percentage)
                    if self.transaction_fee_percentage
                    else 0
                ),
                "fixed": (
                    float(self.transaction_fee_fixed)
                    if self.transaction_fee_fixed
                    else 0
                ),
            },
            "limits": {
                "minimum": float(self.minimum_amount) if self.minimum_amount else 0,
                "maximum": float(self.maximum_amount) if self.maximum_amount else None,
            },
        }
