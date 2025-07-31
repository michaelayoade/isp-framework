from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.billing.billing_type import BillingType
from app.schemas.billing_type import BillingTypeCreate, BillingTypeUpdate
from app.core.exceptions import NotFoundError, DuplicateError, ValidationError
import logging

logger = logging.getLogger(__name__)


class BillingTypeService:
    """Service layer for billing type management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_billing_types(self, active_only: bool = True) -> List[BillingType]:
        """List all billing types, optionally filtering by active status."""
        query = self.db.query(BillingType)
        
        if active_only:
            query = query.filter(BillingType.is_active is True)
        
        billing_types = query.order_by(BillingType.sort_order, BillingType.name).all()
        return billing_types
    
    def get_billing_type(self, billing_type_id: int) -> BillingType:
        """Get a billing type by ID."""
        billing_type = self.db.query(BillingType).filter(BillingType.id == billing_type_id).first()
        if not billing_type:
            raise NotFoundError(f"Billing type with ID {billing_type_id} not found")
        return billing_type
    
    def get_billing_type_by_code(self, code: str) -> Optional[BillingType]:
        """Get a billing type by code."""
        return self.db.query(BillingType).filter(BillingType.code == code).first()
    
    def create_billing_type(self, billing_type_data: BillingTypeCreate) -> BillingType:
        """Create a new billing type."""
        # Check if code already exists
        existing = self.get_billing_type_by_code(billing_type_data.code)
        if existing:
            raise DuplicateError(f"Billing type with code '{billing_type_data.code}' already exists")
        
        # Create billing type
        billing_type_dict = billing_type_data.model_dump()
        billing_type_dict['is_system'] = False  # User-created billing types are not system types
        
        billing_type = BillingType(**billing_type_dict)
        self.db.add(billing_type)
        self.db.commit()
        self.db.refresh(billing_type)
        
        logger.info(f"Created billing type: {billing_type.code}")
        return billing_type
    
    def update_billing_type(self, billing_type_id: int, billing_type_data: BillingTypeUpdate) -> BillingType:
        """Update an existing billing type."""
        billing_type = self.get_billing_type(billing_type_id)
        
        # Check if code is being changed and if it conflicts
        if billing_type_data.code and billing_type_data.code != billing_type.code:
            existing = self.get_billing_type_by_code(billing_type_data.code)
            if existing:
                raise DuplicateError(f"Billing type with code '{billing_type_data.code}' already exists")
        
        # Update fields
        update_data = billing_type_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(billing_type, field, value)
        
        billing_type.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(billing_type)
        
        logger.info(f"Updated billing type {billing_type_id}")
        return billing_type
    
    def delete_billing_type(self, billing_type_id: int):
        """Delete a billing type (only non-system billing types)."""
        billing_type = self.get_billing_type(billing_type_id)
        
        # Check if it's a system billing type
        if billing_type.is_system:
            raise ValidationError(f"System billing type '{billing_type.code}' cannot be deleted")
        
        # Check if it's in use by customers
        try:
            from app.models.customer.base import Customer
            customers_using_type = self.db.query(Customer).filter(
                Customer.billing_type_id == billing_type_id
            ).count()
            
            if customers_using_type > 0:
                raise ValidationError(f"Billing type '{billing_type.code}' is in use by {customers_using_type} customers and cannot be deleted")
        except ImportError:
            # Customer model doesn't have billing_type_id yet, skip this check
            pass
        
        # Check if it's in use by service plans
        try:
            from app.models.service.plan import ServicePlan
            plans_using_type = self.db.query(ServicePlan).filter(
                ServicePlan.billing_type_id == billing_type_id
            ).count()
            
            if plans_using_type > 0:
                raise ValidationError(f"Billing type '{billing_type.code}' is in use by {plans_using_type} service plans and cannot be deleted")
        except ImportError:
            # ServicePlan model doesn't have billing_type_id yet, skip this check
            pass
        
        self.db.delete(billing_type)
        self.db.commit()
        
        logger.info(f"Deleted billing type {billing_type_id}")
    
    def get_default_billing_type(self) -> BillingType:
        """Get the default billing type (recurring)."""
        default_type = self.get_billing_type_by_code('recurring')
        if not default_type:
            # Fallback to first active billing type
            default_type = self.db.query(BillingType).filter(
                BillingType.is_active is True
            ).order_by(BillingType.sort_order).first()
            
            if not default_type:
                raise ValidationError("No active billing types found")
        
        return default_type
    
    def get_recurring_billing_types(self) -> List[BillingType]:
        """Get all recurring billing types."""
        return self.db.query(BillingType).filter(
            BillingType.is_active is True,
            BillingType.is_recurring is True
        ).order_by(BillingType.sort_order).all()
    
    def get_prepaid_billing_types(self) -> List[BillingType]:
        """Get all prepaid billing types."""
        return self.db.query(BillingType).filter(
            BillingType.is_active is True,
            BillingType.requires_prepayment is True
        ).order_by(BillingType.sort_order).all()
    
    def requires_prepayment(self, billing_type_id: int) -> bool:
        """Check if billing type requires prepayment."""
        billing_type = self.get_billing_type(billing_type_id)
        return billing_type.requires_prepayment
    
    def supports_credit_limit(self, billing_type_id: int) -> bool:
        """Check if billing type supports credit limits."""
        billing_type = self.get_billing_type(billing_type_id)
        return billing_type.supports_credit_limit
    
    def get_default_credit_limit(self, billing_type_id: int) -> int:
        """Get default credit limit for billing type."""
        billing_type = self.get_billing_type(billing_type_id)
        return billing_type.default_credit_limit
    
    def get_grace_period_days(self, billing_type_id: int) -> int:
        """Get grace period days for billing type."""
        billing_type = self.get_billing_type(billing_type_id)
        return billing_type.grace_period_days
