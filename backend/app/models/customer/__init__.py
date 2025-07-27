"""
Customer Management Models

This module contains all customer-related models including:
- Core customer information and profiles
- Extended customer features and preferences
- Customer portal configuration
- Customer relationships and hierarchies
"""

from .base import (
    Customer,
    CustomerExtended,
    CustomerLabel,
    CustomerLabelAssociation,
    CustomerInfo,
    CustomerBilling,
    CustomerContact,
    CustomerDocument,
    CustomerNote,
    CustomerBonusTrafficCounter
)
from .portal import PortalConfig, PortalIDHistory

__all__ = [
    # Core Customer Models
    "Customer",
    "CustomerExtended",
    "CustomerLabel",
    "CustomerLabelAssociation",
    "CustomerInfo",
    "CustomerBilling",
    "CustomerContact",
    "CustomerDocument",
    "CustomerNote",
    "CustomerBonusTrafficCounter",
    
    # Portal Management
    "PortalConfig",
    "PortalIDHistory",
]
