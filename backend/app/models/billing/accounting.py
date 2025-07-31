"""
Accounting Entry Models

Models for double-entry bookkeeping and financial accounting.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal

from app.core.database import Base


class AccountingEntry(Base):
    """Double-entry accounting entry model"""
    __tablename__ = "accounting_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String(50), unique=True, nullable=False, index=True)
    entry_date = Column(DateTime(timezone=True), nullable=False)
    
    # Account information
    account_code = Column(String(20), nullable=False, index=True)
    account_name = Column(String(100), nullable=False)
    
    # Transaction details
    description = Column(String(500), nullable=False)
    debit_amount = Column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'))
    credit_amount = Column(DECIMAL(12, 2), nullable=False, default=Decimal('0.00'))
    currency = Column(String(3), nullable=False, default="USD")
    
    # Reference links
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=True)
    
    # Additional information
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="accounting_entries")
    payment = relationship("Payment", back_populates="accounting_entries")
    credit_note = relationship("CreditNote", back_populates="accounting_entries")
    creator = relationship("Administrator", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<AccountingEntry(entry_number='{self.entry_number}', account='{self.account_code}', debit={self.debit_amount}, credit={self.credit_amount})>"
    
    @property
    def balance(self) -> Decimal:
        """Calculate the balance (debit - credit)"""
        return self.debit_amount - self.credit_amount
    
    def is_balanced_entry(self) -> bool:
        """Check if this is a balanced double-entry (exactly one of debit/credit is non-zero)"""
        return (self.debit_amount > 0) != (self.credit_amount > 0)


class ChartOfAccounts(Base):
    """Chart of accounts for accounting structure"""
    __tablename__ = "chart_of_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_code = Column(String(20), unique=True, nullable=False, index=True)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense
    parent_account_code = Column(String(20), ForeignKey("chart_of_accounts.account_code"), nullable=True)
    
    # Account properties
    is_active = Column(String(10), nullable=False, default="true")
    is_system_account = Column(String(10), nullable=False, default="false")
    description = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Self-referential relationship for account hierarchy
    parent_account = relationship("ChartOfAccounts", remote_side=[account_code], back_populates="sub_accounts")
    sub_accounts = relationship("ChartOfAccounts", back_populates="parent_account")
    
    def __repr__(self):
        return f"<ChartOfAccounts(code='{self.account_code}', name='{self.account_name}', type='{self.account_type}')>"
