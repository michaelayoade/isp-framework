"""
Billing Transactions and Balance History

Real-time transaction tracking with comprehensive balance history
and audit trail for all billing operations.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..base import Base
from .enums import TransactionCategory, TransactionType


class BillingTransaction(Base):
    """Billing transaction with real-time balance tracking"""

    __tablename__ = "billing_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True
    )
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )

    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    category = Column(SQLEnum(TransactionCategory), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")

    # Description and reference
    description = Column(String(500), nullable=False)
    reference_number = Column(String(100), index=True)
    external_reference = Column(String(100), index=True)

    # Related entities
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    payment_id = Column(Integer, ForeignKey("payments.id"))
    service_id = Column(Integer)

    # Balance tracking
    balance_before = Column(DECIMAL(12, 2), nullable=False)
    balance_after = Column(DECIMAL(12, 2), nullable=False)

    # Transaction metadata
    processed_by = Column(Integer, ForeignKey("administrators.id"))
    processing_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    effective_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Reversal support
    is_reversed = Column(Boolean, default=False)
    reversed_by_transaction_id = Column(Integer, ForeignKey("billing_transactions.id"))
    reversal_reason = Column(String(200))

    # Metadata
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    billing_account = relationship(
        "CustomerBillingAccount", back_populates="transactions"
    )
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    payment = relationship("Payment", foreign_keys=[payment_id])
    processor = relationship("Administrator", foreign_keys=[processed_by])
    reversed_by = relationship("BillingTransaction", remote_side=[id])

    # Indexes
    __table_args__ = (
        Index(
            "idx_billing_transactions_account_date",
            "billing_account_id",
            "processing_date",
        ),
        Index("idx_billing_transactions_type_category", "transaction_type", "category"),
    )

    def __repr__(self):
        return f"<BillingTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"

    @property
    def is_credit(self):
        """Check if transaction is a credit (increases balance)"""
        return self.transaction_type == TransactionType.CREDIT

    @property
    def is_debit(self):
        """Check if transaction is a debit (decreases balance)"""
        return self.transaction_type == TransactionType.DEBIT

    @property
    def net_amount(self):
        """Get net amount considering transaction type"""
        if self.is_credit:
            return abs(self.amount)
        else:
            return -abs(self.amount)

    def create_reversal(self, reason, processed_by=None):
        """Create a reversal transaction"""
        reversal = BillingTransaction(
            billing_account_id=self.billing_account_id,
            transaction_type=TransactionType.REVERSAL,
            category=self.category,
            amount=self.amount,
            currency=self.currency,
            description=f"Reversal of transaction {self.transaction_id}: {reason}",
            reference_number=(
                f"REV-{self.reference_number}" if self.reference_number else None
            ),
            reversed_by_transaction_id=self.transaction_id,
            reversal_reason=reason,
            processed_by=processed_by,
            balance_before=self.billing_account.current_balance,
            balance_after=self.billing_account.current_balance - self.net_amount,
        )

        # Mark original transaction as reversed
        self.is_reversed = True

        return reversal

    def get_transaction_summary(self):
        """Get transaction summary for reporting"""
        return {
            "transaction_id": str(self.transaction_id),
            "type": self.transaction_type.value,
            "category": self.category.value,
            "amount": float(self.amount),
            "net_amount": float(self.net_amount),
            "currency": self.currency,
            "description": self.description,
            "reference_number": self.reference_number,
            "processing_date": self.processing_date.isoformat(),
            "effective_date": self.effective_date.isoformat(),
            "balance_before": float(self.balance_before),
            "balance_after": float(self.balance_after),
            "is_reversed": self.is_reversed,
        }


class BalanceHistory(Base):
    """Balance history tracking for audit and reporting"""

    __tablename__ = "balance_history"

    id = Column(Integer, primary_key=True, index=True)
    billing_account_id = Column(
        Integer, ForeignKey("customer_billing_accounts.id"), nullable=False
    )

    # Balance snapshot
    balance = Column(DECIMAL(12, 2), nullable=False)
    available_balance = Column(DECIMAL(12, 2), nullable=False)
    reserved_balance = Column(DECIMAL(12, 2), nullable=False)

    # Change details
    change_amount = Column(DECIMAL(12, 2), nullable=False)
    change_reason = Column(String(200), nullable=False)
    transaction_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_transactions.transaction_id")
    )

    # Timestamp
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Metadata
    additional_data = Column(JSONB)

    # Relationships
    billing_account = relationship(
        "CustomerBillingAccount", back_populates="balance_history"
    )
    transaction = relationship("BillingTransaction", foreign_keys=[transaction_id])

    # Indexes
    __table_args__ = (
        Index("idx_balance_history_account_date", "billing_account_id", "recorded_at"),
    )

    def __repr__(self):
        return f"<BalanceHistory(id={self.id}, balance={self.balance}, change={self.change_amount})>"

    def get_balance_snapshot(self):
        """Get balance snapshot for reporting"""
        return {
            "recorded_at": self.recorded_at.isoformat(),
            "balance": float(self.balance),
            "available_balance": float(self.available_balance),
            "reserved_balance": float(self.reserved_balance),
            "change_amount": float(self.change_amount),
            "change_reason": self.change_reason,
            "transaction_id": str(self.transaction_id) if self.transaction_id else None,
        }


class TransactionBatch(Base):
    """Batch processing for multiple transactions"""

    __tablename__ = "transaction_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True
    )
    batch_name = Column(String(100), nullable=False)

    # Batch details
    total_transactions = Column(Integer, default=0)
    successful_transactions = Column(Integer, default=0)
    failed_transactions = Column(Integer, default=0)
    total_amount = Column(DECIMAL(12, 2), default=0)

    # Processing status
    status = Column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, processing, completed, failed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Metadata
    description = Column(String(500))
    processed_by = Column(Integer, ForeignKey("administrators.id"))
    error_log = Column(JSONB)
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    processor = relationship("Administrator", foreign_keys=[processed_by])

    def __repr__(self):
        return f"<TransactionBatch(id={self.id}, name='{self.batch_name}', status={self.status})>"

    @property
    def success_rate(self):
        """Calculate batch success rate"""
        if self.total_transactions == 0:
            return 0
        return (self.successful_transactions / self.total_transactions) * 100

    def get_batch_summary(self):
        """Get batch processing summary"""
        return {
            "batch_id": str(self.batch_id),
            "batch_name": self.batch_name,
            "status": self.status,
            "total_transactions": self.total_transactions,
            "successful_transactions": self.successful_transactions,
            "failed_transactions": self.failed_transactions,
            "success_rate": self.success_rate,
            "total_amount": float(self.total_amount),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "processing_time": (
                (self.completed_at - self.started_at).total_seconds()
                if self.started_at and self.completed_at
                else None
            ),
        }
