"""
Invoicing System

Advanced invoicing with proration support, automated billing cycles,
and comprehensive invoice management for ISP services.
"""

from datetime import datetime, timezone

from sqlalchemy import DECIMAL, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .enums import InvoiceStatus


class Invoice(Base):
    """Invoice with proration and advanced billing features"""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )

    # Invoice dates
    invoice_date = Column(DateTime(timezone=True), nullable=False, index=True)
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    billing_period_start = Column(DateTime(timezone=True), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), nullable=False)

    # Amounts
    subtotal = Column(DECIMAL(12, 2), nullable=False, default=0)
    tax_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    discount_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    adjustment_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    total_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    paid_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    balance_due = Column(DECIMAL(12, 2), nullable=False, default=0)

    # Invoice configuration
    status = Column(
        SQLEnum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT, index=True
    )
    currency = Column(String(3), nullable=False, default="USD")
    tax_rate = Column(DECIMAL(5, 2), default=0)

    # Proration support
    is_prorated = Column(Boolean, default=False)
    proration_factor = Column(DECIMAL(5, 4), default=1.0000)

    # Invoice metadata
    description = Column(Text)
    notes = Column(Text)
    terms_and_conditions = Column(Text)

    # Processing dates
    sent_date = Column(DateTime(timezone=True))
    paid_date = Column(DateTime(timezone=True))
    cancelled_date = Column(DateTime(timezone=True))

    # References
    parent_invoice_id = Column(Integer, ForeignKey("invoices.id"))
    billing_cycle_id = Column(Integer, ForeignKey("billing_cycles.id"))
    template_id = Column(Integer)

    # Automation
    auto_send = Column(Boolean, default=False)
    auto_apply_payments = Column(Boolean, default=True)

    # Metadata
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_account = relationship("CustomerBillingAccount", back_populates="invoices")
    invoice_items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="invoice")
    credit_notes = relationship("CreditNote", back_populates="invoice")
    parent_invoice = relationship("Invoice", remote_side=[id])
    child_invoices = relationship("Invoice", back_populates="parent_invoice")
    billing_cycle = relationship("BillingCycle", foreign_keys=[billing_cycle_id])

    # Indexes
    __table_args__ = (
        Index("idx_invoices_account_date", "billing_account_id", "invoice_date"),
        Index("idx_invoices_status_due", "status", "due_date"),
    )

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount})>"

    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status in [
            InvoiceStatus.PAID,
            InvoiceStatus.CANCELLED,
            InvoiceStatus.REFUNDED,
        ]:
            return False
        return datetime.now(timezone.utc) > self.due_date

    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0
        return (datetime.now(timezone.utc) - self.due_date).days

    @property
    def is_paid(self):
        """Check if invoice is fully paid"""
        return self.status == InvoiceStatus.PAID or self.balance_due <= 0

    @property
    def is_partially_paid(self):
        """Check if invoice is partially paid"""
        return self.paid_amount > 0 and self.balance_due > 0

    def calculate_proration(self, service_start_date, service_end_date):
        """Calculate proration factor for partial billing periods"""
        if not service_start_date or not service_end_date:
            return 1.0000

        total_days = (self.billing_period_end - self.billing_period_start).days
        service_days = (service_end_date - service_start_date).days

        if total_days <= 0:
            return 1.0000

        return min(1.0000, service_days / total_days)

    def apply_payment(self, payment_amount):
        """Apply payment to invoice and update balances"""
        if payment_amount <= 0:
            return False

        # Update paid amount and balance due
        self.paid_amount += payment_amount
        self.balance_due = max(0, self.total_amount - self.paid_amount)

        # Update status based on payment
        if self.balance_due <= 0:
            self.status = InvoiceStatus.PAID
            self.paid_date = datetime.now(timezone.utc)
        elif self.paid_amount > 0:
            self.status = InvoiceStatus.PARTIALLY_PAID

        return True

    def calculate_totals(self):
        """Recalculate invoice totals from line items"""
        self.subtotal = sum(item.line_total for item in self.invoice_items)
        self.tax_amount = sum(item.tax_amount for item in self.invoice_items)
        self.total_amount = (
            self.subtotal
            + self.tax_amount
            - self.discount_amount
            + self.adjustment_amount
        )
        self.balance_due = self.total_amount - self.paid_amount

    def get_invoice_summary(self):
        """Get comprehensive invoice summary"""
        return {
            "invoice_number": self.invoice_number,
            "status": self.status.value,
            "invoice_date": self.invoice_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "billing_period": {
                "start": self.billing_period_start.isoformat(),
                "end": self.billing_period_end.isoformat(),
            },
            "amounts": {
                "subtotal": float(self.subtotal),
                "tax_amount": float(self.tax_amount),
                "discount_amount": float(self.discount_amount),
                "adjustment_amount": float(self.adjustment_amount),
                "total_amount": float(self.total_amount),
                "paid_amount": float(self.paid_amount),
                "balance_due": float(self.balance_due),
            },
            "currency": self.currency,
            "is_overdue": self.is_overdue,
            "days_overdue": self.days_overdue,
            "is_prorated": self.is_prorated,
            "proration_factor": (
                float(self.proration_factor) if self.proration_factor else 1.0
            ),
        }


class InvoiceItem(Base):
    """Invoice line items with proration support"""

    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)

    # Item details
    description = Column(String(500), nullable=False)
    item_type = Column(String(50), nullable=False)
    service_id = Column(Integer)
    product_id = Column(Integer)
    tariff_id = Column(Integer)

    # Pricing
    quantity = Column(DECIMAL(10, 4), nullable=False, default=1)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    discount_percentage = Column(DECIMAL(5, 2), default=0)
    discount_amount = Column(DECIMAL(12, 2), default=0)
    line_total = Column(DECIMAL(12, 2), nullable=False)

    # Tax handling
    taxable = Column(Boolean, default=True)
    tax_rate = Column(DECIMAL(5, 2), default=0)
    tax_amount = Column(DECIMAL(12, 2), default=0)

    # Proration support
    is_prorated = Column(Boolean, default=False)
    proration_factor = Column(DECIMAL(5, 4), default=1.0000)
    original_amount = Column(DECIMAL(12, 2))

    # Service period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Metadata
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, description='{self.description}', total={self.line_total})>"

    def calculate_prorated_amount(self):
        """Calculate prorated amount based on proration factor"""
        if not self.is_prorated or not self.original_amount:
            return self.line_total
        return self.original_amount * self.proration_factor

    def calculate_line_total(self):
        """Calculate line total including discounts and taxes"""
        # Base amount
        base_amount = self.quantity * self.unit_price

        # Apply proration if applicable
        if self.is_prorated and self.proration_factor:
            base_amount *= self.proration_factor

        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = base_amount * (self.discount_percentage / 100)

        # Calculate line total before tax
        self.line_total = base_amount - self.discount_amount

        # Calculate tax if applicable
        if self.taxable and self.tax_rate > 0:
            self.tax_amount = self.line_total * (self.tax_rate / 100)

        return self.line_total

    def get_item_summary(self):
        """Get invoice item summary"""
        return {
            "description": self.description,
            "item_type": self.item_type,
            "quantity": float(self.quantity),
            "unit_price": float(self.unit_price),
            "discount_percentage": (
                float(self.discount_percentage) if self.discount_percentage else 0
            ),
            "discount_amount": (
                float(self.discount_amount) if self.discount_amount else 0
            ),
            "line_total": float(self.line_total),
            "taxable": self.taxable,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "is_prorated": self.is_prorated,
            "proration_factor": (
                float(self.proration_factor) if self.proration_factor else 1.0
            ),
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
            },
        }


class InvoiceTemplate(Base):
    """Invoice templates for automated billing"""

    __tablename__ = "invoice_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)
    template_type = Column(String(50), nullable=False)  # service, product, custom

    # Template configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Content
    header_html = Column(Text)
    footer_html = Column(Text)
    terms_and_conditions = Column(Text)
    payment_instructions = Column(Text)

    # Styling
    css_styles = Column(Text)
    logo_url = Column(String(500))
    color_scheme = Column(JSONB)

    # Metadata
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<InvoiceTemplate(id={self.id}, name='{self.template_name}')>"
