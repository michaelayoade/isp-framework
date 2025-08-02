"""
Bank Account Models

SQLAlchemy models for bank account management in the payment system.
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.ext.declarative import declarative_base

from ..base import Base


class BankAccountOwnerType(enum.Enum):
    """Bank account owner type enumeration."""
    PLATFORM = "PLATFORM"
    RESELLER = "RESELLER"


class BankAccount(Base):
    """
    Bank Account model for platform collections and reseller payouts.
    
    Supports both platform collection accounts (for customer payments)
    and reseller payout accounts (for commission payments).
    """
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    
    # Owner information
    owner_type = Column(Enum(BankAccountOwnerType), nullable=False, index=True)
    owner_id = Column(Integer, nullable=True, index=True)  # NULL for platform accounts
    
    # Bank details
    bank_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False, index=True)
    account_name = Column(String(100), nullable=False)
    bank_code = Column(String(20), nullable=True)
    branch_code = Column(String(20), nullable=True)
    branch_name = Column(String(100), nullable=True)
    
    # Account metadata
    currency = Column(String(3), nullable=False, default="USD")
    country = Column(String(2), nullable=False, default="NG")
    alias = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    
    # Status and verification
    active = Column(Boolean, nullable=False, default=True)
    verified = Column(Boolean, nullable=False, default=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<BankAccount(id={self.id}, owner_type={self.owner_type.value}, account_number={self.account_number[-4:]})>"

    @property
    def masked_account_number(self) -> str:
        """Return masked account number for security."""
        if len(self.account_number) <= 4:
            return "*" * len(self.account_number)
        return "*" * (len(self.account_number) - 4) + self.account_number[-4:]

    @property
    def display_name(self) -> str:
        """Return display name for the account."""
        if self.alias:
            return self.alias
        return f"{self.bank_name} - {self.masked_account_number}"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "owner_type": self.owner_type.value,
            "owner_id": self.owner_id,
            "bank_name": self.bank_name,
            "account_number": self.account_number,
            "account_name": self.account_name,
            "bank_code": self.bank_code,
            "branch_code": self.branch_code,
            "branch_name": self.branch_name,
            "currency": self.currency,
            "country": self.country,
            "alias": self.alias,
            "description": self.description,
            "active": self.active,
            "verified": self.verified,
            "verification_date": self.verification_date.isoformat() if self.verification_date else None,
            "verification_notes": self.verification_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "masked_account_number": self.masked_account_number,
            "display_name": self.display_name
        }
