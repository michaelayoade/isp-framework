"""
Tax Rate Management Models

Models for managing tax rates, tax calculations, and tax reporting.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from app.core.database import Base
from .enums import TransactionCategory


class TaxRate(Base):
    """Tax rate configuration model"""
    __tablename__ = "tax_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    rate = Column(DECIMAL(5, 4), nullable=False)  # e.g., 0.1500 for 15%
    tax_type = Column(String(50), nullable=False, default="VAT")  # VAT, GST, Sales Tax, etc.
    
    # Geographic scope
    country_code = Column(String(3), nullable=False, default="US")
    state_province = Column(String(50))
    city = Column(String(100))
    
    # Validity period
    effective_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expiry_date = Column(DateTime(timezone=True))
    
    # Status and configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    applies_to_services = Column(Boolean, default=True, nullable=False)
    applies_to_products = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("Administrator", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<TaxRate(name='{self.name}', rate={self.rate}, type='{self.tax_type}')>"
    
    @property
    def rate_percentage(self) -> Decimal:
        """Get rate as percentage (e.g., 15.00 for 0.1500)"""
        return self.rate * 100
    
    def calculate_tax(self, amount: Decimal) -> Decimal:
        """Calculate tax amount for given base amount"""
        return amount * self.rate
    
    def is_valid_for_date(self, check_date: datetime = None) -> bool:
        """Check if tax rate is valid for given date"""
        if check_date is None:
            check_date = datetime.now(timezone.utc)
            
        if not self.is_active:
            return False
            
        if check_date < self.effective_date:
            return False
            
        if self.expiry_date and check_date > self.expiry_date:
            return False
            
        return True


class TaxCalculation(Base):
    """Tax calculation record for transactions"""
    __tablename__ = "tax_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to the transaction/invoice
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    invoice_item_id = Column(Integer, ForeignKey("invoice_items.id"))
    transaction_id = Column(Integer, ForeignKey("billing_transactions.id"))
    
    # Tax details
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id"), nullable=False)
    base_amount = Column(DECIMAL(12, 2), nullable=False)
    tax_amount = Column(DECIMAL(12, 2), nullable=False)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # Calculation metadata
    calculation_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    tax_jurisdiction = Column(String(100))
    
    # Relationships
    tax_rate = relationship("TaxRate")
    invoice = relationship("Invoice", back_populates="tax_calculations")
    
    def __repr__(self):
        return f"<TaxCalculation(base={self.base_amount}, tax={self.tax_amount}, rate_id={self.tax_rate_id})>"


class TaxExemption(Base):
    """Tax exemption records for customers or services"""
    __tablename__ = "tax_exemptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Exemption scope
    customer_id = Column(Integer, ForeignKey("customers.id"))
    service_type = Column(String(50))  # internet, voice, bundle, etc.
    
    # Exemption details
    exemption_type = Column(String(50), nullable=False)  # full, partial, category
    exemption_rate = Column(DECIMAL(5, 4), default=Decimal('1.0000'))  # 1.0 = full exemption
    tax_category = Column(String(50))  # Which taxes this exemption applies to
    
    # Documentation
    exemption_reason = Column(String(200), nullable=False)
    certificate_number = Column(String(100))
    certificate_file_path = Column(String(500))
    
    # Validity
    effective_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expiry_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Approval workflow
    approved_by = Column(Integer, ForeignKey("administrators.id"))
    approved_at = Column(DateTime(timezone=True))
    
    # Audit
    created_by = Column(Integer, ForeignKey("administrators.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    approver = relationship("Administrator", foreign_keys=[approved_by])
    creator = relationship("Administrator", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<TaxExemption(customer_id={self.customer_id}, type='{self.exemption_type}', rate={self.exemption_rate})>"
    
    def is_valid_for_date(self, check_date: datetime = None) -> bool:
        """Check if exemption is valid for given date"""
        if check_date is None:
            check_date = datetime.now(timezone.utc)
            
        if not self.is_active:
            return False
            
        if check_date < self.effective_date:
            return False
            
        if self.expiry_date and check_date > self.expiry_date:
            return False
            
        return True
