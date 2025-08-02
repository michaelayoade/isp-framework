"""
Gateway Models

SQLAlchemy models for payment gateway management.
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB

from ..base import Base


class GatewayType(enum.Enum):
    """Payment gateway type enumeration."""
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    STRIPE = "stripe"
    PAYPAL = "paypal"
    SQUARE = "square"
    RAZORPAY = "razorpay"
    OTHER = "other"


class Gateway(Base):
    """
    Payment Gateway model for managing payment processors.
    
    Stores gateway configuration and credentials securely.
    """
    __tablename__ = "gateways"

    id = Column(Integer, primary_key=True, index=True)
    
    # Gateway details
    name = Column(String(100), nullable=False, unique=True, index=True)
    gateway_type = Column(Enum(GatewayType), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    base_url = Column(String(255), nullable=True)
    api_version = Column(String(20), nullable=True)
    supported_currencies = Column(JSONB, nullable=True, default=["USD", "NGN"])
    supported_methods = Column(JSONB, nullable=True, default=["card", "bank_transfer"])
    
    # Credentials (encrypted)
    public_key = Column(Text, nullable=True)
    secret_key = Column(Text, nullable=True)  # Should be encrypted
    webhook_secret = Column(Text, nullable=True)  # Should be encrypted
    
    # Settings
    active = Column(Boolean, nullable=False, default=True)
    test_mode = Column(Boolean, nullable=False, default=True)
    auto_capture = Column(Boolean, nullable=False, default=True)
    
    # Fee configuration
    fixed_fee = Column(DECIMAL(10, 2), nullable=True, default=0)
    percentage_fee = Column(DECIMAL(5, 4), nullable=True, default=0)  # e.g., 0.029 for 2.9%
    
    # Limits
    min_amount = Column(DECIMAL(10, 2), nullable=True)
    max_amount = Column(DECIMAL(10, 2), nullable=True)
    
    # Metadata
    webhook_url = Column(String(255), nullable=True)
    callback_url = Column(String(255), nullable=True)
    
    # Status tracking
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(20), nullable=True, default="unknown")
    
    # Tenant support
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Gateway(id={self.id}, name={self.name}, type={self.gateway_type.value}, active={self.active})>"

    def to_dict(self, include_secrets=False):
        """Convert to dictionary representation."""
        data = {
            "id": self.id,
            "name": self.name,
            "gateway_type": self.gateway_type.value,
            "display_name": self.display_name,
            "description": self.description,
            "base_url": self.base_url,
            "api_version": self.api_version,
            "supported_currencies": self.supported_currencies,
            "supported_methods": self.supported_methods,
            "active": self.active,
            "test_mode": self.test_mode,
            "auto_capture": self.auto_capture,
            "fixed_fee": float(self.fixed_fee) if self.fixed_fee else None,
            "percentage_fee": float(self.percentage_fee) if self.percentage_fee else None,
            "min_amount": float(self.min_amount) if self.min_amount else None,
            "max_amount": float(self.max_amount) if self.max_amount else None,
            "webhook_url": self.webhook_url,
            "callback_url": self.callback_url,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_secrets:
            data.update({
                "public_key": self.public_key,
                "secret_key": self.secret_key,
                "webhook_secret": self.webhook_secret
            })
        else:
            # Mask sensitive data
            data.update({
                "public_key": f"pk_***{self.public_key[-4:]}" if self.public_key else None,
                "secret_key": "sk_***" if self.secret_key else None,
                "webhook_secret": "whsec_***" if self.webhook_secret else None
            })
        
        return data
