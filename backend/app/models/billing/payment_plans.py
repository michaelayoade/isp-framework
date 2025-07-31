"""
Payment Plans and Installment Management

Comprehensive payment plan system with automated installment tracking,
late fee management, and flexible payment scheduling.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .enums import InstallmentStatus, PaymentPlanStatus


class PaymentPlan(Base):
    """Payment plans for installment payments"""

    __tablename__ = "payment_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_number = Column(String(50), unique=True, nullable=False, index=True)
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )
    invoice_id = Column(Integer, ForeignKey("invoices.id"))

    # Plan details
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    down_payment = Column(DECIMAL(12, 2), default=0)
    remaining_amount = Column(DECIMAL(12, 2), nullable=False)
    installment_amount = Column(DECIMAL(12, 2), nullable=False)
    number_of_installments = Column(Integer, nullable=False)

    # Schedule
    start_date = Column(DateTime(timezone=True), nullable=False)
    frequency = Column(
        String(20), nullable=False, default="monthly"
    )  # monthly, weekly, bi-weekly

    # Status
    status = Column(
        SQLEnum(PaymentPlanStatus),
        nullable=False,
        default=PaymentPlanStatus.ACTIVE,
        index=True,
    )
    created_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_date = Column(DateTime(timezone=True))
    defaulted_date = Column(DateTime(timezone=True))
    cancelled_date = Column(DateTime(timezone=True))

    # Terms
    interest_rate = Column(DECIMAL(5, 2), default=0)
    late_fee = Column(DECIMAL(12, 2), default=0)
    grace_period_days = Column(Integer, default=5)

    # Auto-payment
    auto_pay_enabled = Column(Boolean, default=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))

    # Metadata
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_account = relationship(
        "CustomerBillingAccount", back_populates="payment_plans"
    )
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    installments = relationship(
        "PaymentPlanInstallment",
        back_populates="payment_plan",
        cascade="all, delete-orphan",
    )
    payment_method = relationship("PaymentMethod", foreign_keys=[payment_method_id])
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<PaymentPlan(id={self.id}, number='{self.plan_number}', total={self.total_amount})>"

    @property
    def is_current(self):
        """Check if payment plan is current (no overdue installments)"""
        overdue_installments = [
            i
            for i in self.installments
            if i.status == InstallmentStatus.PENDING and i.is_overdue
        ]
        return len(overdue_installments) == 0

    @property
    def paid_amount(self):
        """Calculate total amount paid so far"""
        return sum(i.paid_amount for i in self.installments if i.paid_amount)

    @property
    def remaining_balance(self):
        """Calculate remaining balance"""
        return self.total_amount - self.paid_amount

    @property
    def next_installment(self):
        """Get next pending installment"""
        pending_installments = [
            i for i in self.installments if i.status == InstallmentStatus.PENDING
        ]
        if pending_installments:
            return min(pending_installments, key=lambda x: x.due_date)
        return None

    @property
    def overdue_installments(self):
        """Get all overdue installments"""
        return [i for i in self.installments if i.is_overdue]

    def generate_installments(self):
        """Generate installment schedule"""
        installments = []
        current_date = self.start_date

        for i in range(self.number_of_installments):
            installment = PaymentPlanInstallment(
                payment_plan_id=self.id,
                installment_number=i + 1,
                due_date=current_date,
                amount=self.installment_amount,
                balance_due=self.installment_amount,
            )
            installments.append(installment)

            # Calculate next due date based on frequency
            if self.frequency == "weekly":
                current_date += timedelta(weeks=1)
            elif self.frequency == "bi-weekly":
                current_date += timedelta(weeks=2)
            else:  # monthly
                # Add one month (approximate)
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        return installments

    def calculate_total_with_interest(self):
        """Calculate total amount including interest"""
        if self.interest_rate <= 0:
            return self.remaining_amount

        # Simple interest calculation
        interest_amount = self.remaining_amount * (self.interest_rate / 100)
        return self.remaining_amount + interest_amount

    def mark_as_completed(self):
        """Mark payment plan as completed"""
        self.status = PaymentPlanStatus.COMPLETED
        self.completed_date = datetime.now(timezone.utc)

    def mark_as_defaulted(self, reason=None):
        """Mark payment plan as defaulted"""
        self.status = PaymentPlanStatus.DEFAULTED
        self.defaulted_date = datetime.now(timezone.utc)
        if reason:
            self.notes = (
                f"{self.notes}\nDefaulted: {reason}"
                if self.notes
                else f"Defaulted: {reason}"
            )

    def get_plan_summary(self):
        """Get comprehensive payment plan summary"""
        return {
            "plan_number": self.plan_number,
            "status": self.status.value,
            "total_amount": float(self.total_amount),
            "down_payment": float(self.down_payment),
            "remaining_amount": float(self.remaining_amount),
            "installment_amount": float(self.installment_amount),
            "number_of_installments": self.number_of_installments,
            "paid_amount": float(self.paid_amount),
            "remaining_balance": float(self.remaining_balance),
            "start_date": self.start_date.isoformat(),
            "frequency": self.frequency,
            "interest_rate": float(self.interest_rate) if self.interest_rate else 0,
            "late_fee": float(self.late_fee) if self.late_fee else 0,
            "grace_period_days": self.grace_period_days,
            "is_current": self.is_current,
            "auto_pay_enabled": self.auto_pay_enabled,
            "completed_date": (
                self.completed_date.isoformat() if self.completed_date else None
            ),
            "defaulted_date": (
                self.defaulted_date.isoformat() if self.defaulted_date else None
            ),
        }


class PaymentPlanInstallment(Base):
    """Individual installments for payment plans"""

    __tablename__ = "payment_plan_installments"

    id = Column(Integer, primary_key=True, index=True)
    payment_plan_id = Column(Integer, ForeignKey("payment_plans.id"), nullable=False)
    installment_number = Column(Integer, nullable=False)

    # Installment details
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    paid_amount = Column(DECIMAL(12, 2), default=0)
    balance_due = Column(DECIMAL(12, 2), nullable=False)

    # Status
    status = Column(
        SQLEnum(InstallmentStatus),
        nullable=False,
        default=InstallmentStatus.PENDING,
        index=True,
    )
    paid_date = Column(DateTime(timezone=True))

    # Late fees
    late_fee_applied = Column(DECIMAL(12, 2), default=0)
    late_fee_date = Column(DateTime(timezone=True))

    # Payment tracking
    payment_id = Column(Integer, ForeignKey("payments.id"))

    # Retry tracking for auto-pay
    auto_pay_attempts = Column(Integer, default=0)
    last_auto_pay_attempt = Column(DateTime(timezone=True))

    # Metadata
    notes = Column(Text)
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    payment_plan = relationship("PaymentPlan", back_populates="installments")
    payment = relationship("Payment", foreign_keys=[payment_id])

    # Indexes
    __table_args__ = (
        Index("idx_installments_plan_due", "payment_plan_id", "due_date"),
        Index("idx_installments_status_due", "status", "due_date"),
    )

    def __repr__(self):
        return f"<PaymentPlanInstallment(id={self.id}, number={self.installment_number}, amount={self.amount})>"

    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        if self.status != InstallmentStatus.PENDING:
            return False

        grace_period = timedelta(days=self.payment_plan.grace_period_days)
        return datetime.now(timezone.utc) > (self.due_date + grace_period)

    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue:
            return 0

        grace_period = timedelta(days=self.payment_plan.grace_period_days)
        overdue_date = self.due_date + grace_period
        return (datetime.now(timezone.utc) - overdue_date).days

    @property
    def is_paid(self):
        """Check if installment is fully paid"""
        return self.status == InstallmentStatus.PAID or self.balance_due <= 0

    def apply_payment(self, payment_amount, payment_id=None):
        """Apply payment to installment"""
        if payment_amount <= 0:
            return False

        # Update paid amount and balance
        self.paid_amount += payment_amount
        self.balance_due = max(
            0, self.amount + self.late_fee_applied - self.paid_amount
        )

        # Update status
        if self.balance_due <= 0:
            self.status = InstallmentStatus.PAID
            self.paid_date = datetime.now(timezone.utc)

        # Link payment
        if payment_id:
            self.payment_id = payment_id

        return True

    def apply_late_fee(self):
        """Apply late fee if installment is overdue"""
        if not self.is_overdue or self.late_fee_applied > 0:
            return False

        if self.payment_plan.late_fee > 0:
            self.late_fee_applied = self.payment_plan.late_fee
            self.late_fee_date = datetime.now(timezone.utc)
            self.balance_due += self.late_fee_applied
            return True

        return False

    def mark_as_defaulted(self):
        """Mark installment as defaulted"""
        self.status = InstallmentStatus.DEFAULTED

    def get_installment_summary(self):
        """Get installment summary"""
        return {
            "installment_number": self.installment_number,
            "status": self.status.value,
            "due_date": self.due_date.isoformat(),
            "amount": float(self.amount),
            "paid_amount": float(self.paid_amount),
            "balance_due": float(self.balance_due),
            "late_fee_applied": (
                float(self.late_fee_applied) if self.late_fee_applied else 0
            ),
            "is_overdue": self.is_overdue,
            "days_overdue": self.days_overdue,
            "is_paid": self.is_paid,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "late_fee_date": (
                self.late_fee_date.isoformat() if self.late_fee_date else None
            ),
        }


class PaymentPlanTemplate(Base):
    """Templates for creating payment plans"""

    __tablename__ = "payment_plan_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False, unique=True)

    # Template configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Plan defaults
    default_installments = Column(Integer, nullable=False)
    default_frequency = Column(String(20), nullable=False, default="monthly")
    default_interest_rate = Column(DECIMAL(5, 2), default=0)
    default_late_fee = Column(DECIMAL(12, 2), default=0)
    default_grace_period = Column(Integer, default=5)

    # Eligibility criteria
    minimum_amount = Column(DECIMAL(12, 2))
    maximum_amount = Column(DECIMAL(12, 2))
    minimum_down_payment_percentage = Column(DECIMAL(5, 2), default=0)
    maximum_installments = Column(Integer)

    # Auto-approval settings
    auto_approve = Column(Boolean, default=False)
    auto_approve_limit = Column(DECIMAL(12, 2))

    # Metadata
    description = Column(Text)
    terms_and_conditions = Column(Text)
    created_by = Column(Integer, ForeignKey("administrators.id"))
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])

    def __repr__(self):
        return f"<PaymentPlanTemplate(id={self.id}, name='{self.template_name}')>"

    def is_amount_eligible(self, amount):
        """Check if amount is eligible for this template"""
        if self.minimum_amount and amount < self.minimum_amount:
            return False
        if self.maximum_amount and amount > self.maximum_amount:
            return False
        return True

    def calculate_minimum_down_payment(self, total_amount):
        """Calculate minimum down payment required"""
        if not self.minimum_down_payment_percentage:
            return 0
        return total_amount * (self.minimum_down_payment_percentage / 100)

    def can_auto_approve(self, amount):
        """Check if plan can be auto-approved"""
        return (
            self.auto_approve
            and self.auto_approve_limit
            and amount <= self.auto_approve_limit
        )

    def get_template_summary(self):
        """Get template configuration summary"""
        return {
            "template_name": self.template_name,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "defaults": {
                "installments": self.default_installments,
                "frequency": self.default_frequency,
                "interest_rate": (
                    float(self.default_interest_rate)
                    if self.default_interest_rate
                    else 0
                ),
                "late_fee": (
                    float(self.default_late_fee) if self.default_late_fee else 0
                ),
                "grace_period": self.default_grace_period,
            },
            "eligibility": {
                "minimum_amount": (
                    float(self.minimum_amount) if self.minimum_amount else None
                ),
                "maximum_amount": (
                    float(self.maximum_amount) if self.maximum_amount else None
                ),
                "minimum_down_payment_percentage": (
                    float(self.minimum_down_payment_percentage)
                    if self.minimum_down_payment_percentage
                    else 0
                ),
                "maximum_installments": self.maximum_installments,
            },
            "auto_approval": {
                "enabled": self.auto_approve,
                "limit": (
                    float(self.auto_approve_limit) if self.auto_approve_limit else None
                ),
            },
        }
