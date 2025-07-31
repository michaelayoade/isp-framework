"""
Credit Notes System

Automated credit note processing with approval workflows
and comprehensive adjustment management.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .enums import CreditNoteReason


class CreditNote(Base):
    """Credit notes with automated processing"""

    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True, index=True)
    credit_note_number = Column(String(50), unique=True, nullable=False, index=True)
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )
    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    # Credit note details
    credit_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    reason = Column(SQLEnum(CreditNoteReason), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Processing
    status = Column(String(20), nullable=False, default="active", index=True)
    applied_date = Column(DateTime(timezone=True))
    auto_apply = Column(Boolean, default=True)

    # Approval workflow
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    approved_date = Column(DateTime(timezone=True))
    approval_notes = Column(Text)

    # Service reference
    service_id = Column(Integer)
    service_period_start = Column(DateTime(timezone=True))
    service_period_end = Column(DateTime(timezone=True))

    # Metadata
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_account = relationship("CustomerBillingAccount")
    invoice = relationship("Invoice", back_populates="credit_notes")
    approver = relationship("Administrator", foreign_keys=[approved_by])
    creator = relationship("Administrator", foreign_keys=[created_by])
    accounting_entries = relationship("AccountingEntry", back_populates="credit_note")

    def __repr__(self):
        return f"<CreditNote(id={self.id}, number='{self.credit_note_number}', amount={self.amount})>"

    @property
    def is_approved(self):
        """Check if credit note is approved"""
        return not self.requires_approval or (
            self.approved_by is not None and self.approved_date is not None
        )

    @property
    def is_applied(self):
        """Check if credit note has been applied"""
        return self.applied_date is not None

    @property
    def can_be_applied(self):
        """Check if credit note can be applied"""
        return self.status == "active" and self.is_approved and not self.is_applied

    def approve(self, approver_id, approval_notes=None):
        """Approve the credit note"""
        if not self.requires_approval:
            return True

        self.approved_by = approver_id
        self.approved_date = datetime.now(timezone.utc)
        if approval_notes:
            self.approval_notes = approval_notes

        # Auto-apply if configured
        if self.auto_apply:
            return self.apply_credit()

        return True

    def apply_credit(self):
        """Apply credit note to customer balance"""
        if not self.can_be_applied:
            return False

        # Update billing account balance
        self.billing_account.current_balance += self.amount
        self.billing_account.available_balance = (
            self.billing_account.calculate_available_balance()
        )

        # Create transaction record
        from .transactions import (
            BillingTransaction,
            TransactionCategory,
            TransactionType,
        )

        BillingTransaction(
            billing_account_id=self.billing_account_id,
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.ADJUSTMENT,
            amount=self.amount,
            currency=self.currency,
            description=f"Credit Note {self.credit_note_number}: {self.description}",
            reference_number=self.credit_note_number,
            balance_before=self.billing_account.current_balance - self.amount,
            balance_after=self.billing_account.current_balance,
        )

        # Mark as applied
        self.applied_date = datetime.now(timezone.utc)

        return True

    def get_credit_note_summary(self):
        """Get comprehensive credit note summary"""
        return {
            "credit_note_number": self.credit_note_number,
            "status": self.status,
            "amount": float(self.amount),
            "currency": self.currency,
            "reason": self.reason.value,
            "description": self.description,
            "credit_date": self.credit_date.isoformat(),
            "applied_date": (
                self.applied_date.isoformat() if self.applied_date else None
            ),
            "is_approved": self.is_approved,
            "is_applied": self.is_applied,
            "can_be_applied": self.can_be_applied,
            "requires_approval": self.requires_approval,
            "approved_date": (
                self.approved_date.isoformat() if self.approved_date else None
            ),
            "service_period": {
                "start": (
                    self.service_period_start.isoformat()
                    if self.service_period_start
                    else None
                ),
                "end": (
                    self.service_period_end.isoformat()
                    if self.service_period_end
                    else None
                ),
            },
        }


class CreditNoteTemplate(Base):
    """Templates for automated credit note generation"""

    __tablename__ = "credit_note_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)
    reason = Column(SQLEnum(CreditNoteReason), nullable=False)

    # Template configuration
    is_active = Column(Boolean, default=True)
    auto_apply = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)

    # Amount calculation
    amount_type = Column(
        String(20), nullable=False, default="fixed"
    )  # fixed, percentage, calculated
    fixed_amount = Column(DECIMAL(12, 2))
    percentage_amount = Column(DECIMAL(5, 2))

    # Conditions
    minimum_amount = Column(DECIMAL(12, 2))
    maximum_amount = Column(DECIMAL(12, 2))
    applicable_services = Column(JSONB)  # List of service types

    # Content
    description_template = Column(Text, nullable=False)
    notes_template = Column(Text)

    # Metadata
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<CreditNoteTemplate(id={self.id}, name='{self.template_name}')>"

    def calculate_amount(self, base_amount):
        """Calculate credit amount based on template configuration"""
        if self.amount_type == "fixed":
            amount = self.fixed_amount or 0
        elif self.amount_type == "percentage":
            amount = (
                base_amount * (self.percentage_amount / 100)
                if self.percentage_amount
                else 0
            )
        else:
            # For calculated amounts, return base amount (custom logic can be implemented)
            amount = base_amount

        # Apply limits
        if self.minimum_amount and amount < self.minimum_amount:
            amount = self.minimum_amount
        if self.maximum_amount and amount > self.maximum_amount:
            amount = self.maximum_amount

        return amount

    def is_applicable_to_service(self, service_type):
        """Check if template applies to given service type"""
        if not self.applicable_services:
            return True  # Apply to all services if not specified
        return service_type in self.applicable_services

    def generate_description(self, **kwargs):
        """Generate description from template"""
        try:
            return self.description_template.format(**kwargs)
        except KeyError:
            return self.description_template

    def get_template_summary(self):
        """Get template configuration summary"""
        return {
            "template_name": self.template_name,
            "reason": self.reason.value,
            "is_active": self.is_active,
            "auto_apply": self.auto_apply,
            "requires_approval": self.requires_approval,
            "amount_type": self.amount_type,
            "fixed_amount": float(self.fixed_amount) if self.fixed_amount else None,
            "percentage_amount": (
                float(self.percentage_amount) if self.percentage_amount else None
            ),
            "limits": {
                "minimum": float(self.minimum_amount) if self.minimum_amount else None,
                "maximum": float(self.maximum_amount) if self.maximum_amount else None,
            },
            "applicable_services": self.applicable_services,
        }


class CreditNoteApproval(Base):
    """Credit note approval workflow tracking"""

    __tablename__ = "credit_note_approvals"

    id = Column(Integer, primary_key=True, index=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=False)

    # Approval details
    requested_by = Column(Integer, ForeignKey("administrators.id"), nullable=False)
    requested_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Approval status
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    approval_date = Column(DateTime(timezone=True))

    # Comments
    request_notes = Column(Text)
    approval_notes = Column(Text)
    rejection_reason = Column(Text)

    # Metadata
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    credit_note = relationship("CreditNote")
    requester = relationship("Administrator", foreign_keys=[requested_by])
    approver = relationship("Administrator", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<CreditNoteApproval(id={self.id}, status='{self.status}')>"

    @property
    def is_pending(self):
        """Check if approval is pending"""
        return self.status == "pending"

    @property
    def is_approved(self):
        """Check if approval was granted"""
        return self.status == "approved"

    @property
    def is_rejected(self):
        """Check if approval was rejected"""
        return self.status == "rejected"

    def approve(self, approver_id, approval_notes=None):
        """Approve the credit note"""
        self.status = "approved"
        self.approved_by = approver_id
        self.approval_date = datetime.now(timezone.utc)
        if approval_notes:
            self.approval_notes = approval_notes

    def reject(self, approver_id, rejection_reason):
        """Reject the credit note"""
        self.status = "rejected"
        self.approved_by = approver_id
        self.approval_date = datetime.now(timezone.utc)
        self.rejection_reason = rejection_reason

    def get_approval_summary(self):
        """Get approval workflow summary"""
        return {
            "status": self.status,
            "requested_date": self.requested_date.isoformat(),
            "approval_date": (
                self.approval_date.isoformat() if self.approval_date else None
            ),
            "request_notes": self.request_notes,
            "approval_notes": self.approval_notes,
            "rejection_reason": self.rejection_reason,
            "is_pending": self.is_pending,
            "is_approved": self.is_approved,
            "is_rejected": self.is_rejected,
        }
