"""
Customer Billing Accounts

Customer billing account management with prepaid/postpaid support,
real-time balance tracking, and advanced account configuration.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..base import Base
from .enums import BillingType, AccountStatus, BillingCycleType


class CustomerBillingAccount(Base):
    """Customer billing account with prepaid/postpaid support"""
    __tablename__ = "customer_billing_accounts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, unique=True)
    account_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Billing configuration
    billing_type = Column(SQLEnum(BillingType), nullable=False, default=BillingType.POSTPAID)
    billing_cycle = Column(SQLEnum(BillingCycleType), nullable=False, default=BillingCycleType.MONTHLY)
    billing_day = Column(Integer, default=1)  # Day of month for billing
    
    # Account status and limits
    status = Column(SQLEnum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE, index=True)
    credit_limit = Column(DECIMAL(12, 2), default=0)  # For postpaid accounts
    minimum_balance = Column(DECIMAL(12, 2), default=0)  # For prepaid accounts
    
    # Balance tracking
    current_balance = Column(DECIMAL(12, 2), nullable=False, default=0, index=True)
    available_balance = Column(DECIMAL(12, 2), nullable=False, default=0)
    reserved_balance = Column(DECIMAL(12, 2), nullable=False, default=0)
    
    # Billing preferences
    currency = Column(String(3), nullable=False, default="USD")
    tax_exempt = Column(Boolean, default=False)
    auto_pay_enabled = Column(Boolean, default=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    
    # Dunning configuration
    dunning_enabled = Column(Boolean, default=True)
    grace_period_days = Column(Integer, default=7)
    suspension_threshold = Column(DECIMAL(12, 2), default=0)
    termination_threshold = Column(DECIMAL(12, 2), default=0)
    
    # Timestamps
    last_billed_date = Column(DateTime(timezone=True))
    next_billing_date = Column(DateTime(timezone=True))
    suspended_date = Column(DateTime(timezone=True))
    terminated_date = Column(DateTime(timezone=True))
    
    # Metadata
    billing_address = Column(JSONB)
    billing_contact = Column(JSONB)
    additional_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="billing_account")
    transactions = relationship("BillingTransaction", back_populates="billing_account", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="billing_account")
    payment_plans = relationship("PaymentPlan", back_populates="billing_account")
    dunning_cases = relationship("DunningCase", back_populates="billing_account")
    balance_history = relationship("BalanceHistory", back_populates="billing_account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CustomerBillingAccount(id={self.id}, account_number='{self.account_number}', balance={self.current_balance})>"

    @property
    def is_prepaid(self):
        """Check if account is prepaid"""
        return self.billing_type in [BillingType.PREPAID, BillingType.HYBRID]

    @property
    def is_postpaid(self):
        """Check if account is postpaid"""
        return self.billing_type in [BillingType.POSTPAID, BillingType.HYBRID]

    @property
    def has_sufficient_balance(self):
        """Check if account has sufficient balance for services"""
        if self.billing_type == BillingType.PREPAID:
            return self.available_balance > self.minimum_balance
        elif self.billing_type == BillingType.POSTPAID:
            return self.current_balance > -self.credit_limit
        else:  # HYBRID
            return self.available_balance > self.minimum_balance or self.current_balance > -self.credit_limit

    def calculate_available_balance(self):
        """Calculate available balance considering reserved amounts"""
        return self.current_balance - self.reserved_balance

    def is_suspended_due_to_balance(self):
        """Check if account should be suspended due to balance"""
        return self.current_balance <= self.suspension_threshold

    def is_terminated_due_to_balance(self):
        """Check if account should be terminated due to balance"""
        return self.current_balance <= self.termination_threshold

    def update_balance(self, amount, description="Balance update"):
        """Update account balance and create history record"""
        self.current_balance += amount
        self.available_balance = self.calculate_available_balance()
        
        # Create balance history record
        from .transactions import BalanceHistory
        history = BalanceHistory(
            billing_account_id=self.id,
            balance=self.current_balance,
            available_balance=self.available_balance,
            reserved_balance=self.reserved_balance,
            change_amount=amount,
            change_reason=description
        )
        return history

    def reserve_balance(self, amount):
        """Reserve balance for pending transactions"""
        if self.available_balance >= amount:
            self.reserved_balance += amount
            self.available_balance -= amount
            return True
        return False

    def release_reserved_balance(self, amount):
        """Release reserved balance"""
        release_amount = min(amount, self.reserved_balance)
        self.reserved_balance -= release_amount
        self.available_balance += release_amount
        return release_amount

    def get_account_summary(self):
        """Get comprehensive account summary"""
        return {
            "account_number": self.account_number,
            "billing_type": self.billing_type.value,
            "status": self.status.value,
            "current_balance": float(self.current_balance),
            "available_balance": float(self.available_balance),
            "reserved_balance": float(self.reserved_balance),
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0,
            "minimum_balance": float(self.minimum_balance) if self.minimum_balance else 0,
            "currency": self.currency,
            "billing_cycle": self.billing_cycle.value,
            "billing_day": self.billing_day,
            "auto_pay_enabled": self.auto_pay_enabled,
            "dunning_enabled": self.dunning_enabled,
            "last_billed_date": self.last_billed_date.isoformat() if self.last_billed_date else None,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None
        }
