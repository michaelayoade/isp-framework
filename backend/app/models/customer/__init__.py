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
    CustomerBilling,
    CustomerBonusTrafficCounter,
    CustomerContact,
    CustomerDocument,
    CustomerExtended,
    CustomerInfo,
    CustomerLabel,
    CustomerLabelAssociation,
    CustomerNote,
)
from .portal import PortalConfig, PortalIDHistory
from .status import CustomerStatus

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
    # Portal Models
    "PortalConfig",
    "PortalIDHistory",
    # Status Models
    "CustomerStatus",
]
