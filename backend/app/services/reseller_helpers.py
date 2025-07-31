"""
Reseller Service Helper Methods

Helper methods for billing integration in reseller service.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.billing import CustomerBillingAccount, Payment
from app.models.services import CustomerService

logger = logging.getLogger(__name__)


def get_customer_services_count(db: Session, customer_id: int) -> int:
    """Get the number of active services for a customer"""
    try:
        count = db.query(CustomerService).filter(
            CustomerService.customer_id == customer_id,
            CustomerService.is_active is True
        ).count()
        return count
    except Exception as e:
        logger.warning(f"Error getting service count for customer {customer_id}: {e}")
        return 0


def get_customer_monthly_revenue(db: Session, customer_id: int) -> float:
    """Get the monthly revenue from a customer's services"""
    try:
        # Get customer's billing account
        billing_account = db.query(CustomerBillingAccount).filter(
            CustomerBillingAccount.customer_id == customer_id
        ).first()
        
        if not billing_account:
            return 0.0
        
        # Calculate monthly revenue from active services
        monthly_revenue = db.query(func.sum(CustomerService.monthly_fee)).filter(
            CustomerService.customer_id == customer_id,
            CustomerService.is_active is True
        ).scalar()
        
        return float(monthly_revenue or 0.0)
    except Exception as e:
        logger.warning(f"Error getting monthly revenue for customer {customer_id}: {e}")
        return 0.0


def get_customer_last_payment_date(db: Session, customer_id: int) -> Optional[datetime]:
    """Get the date of the customer's last payment"""
    try:
        # Get customer's billing account
        billing_account = db.query(CustomerBillingAccount).filter(
            CustomerBillingAccount.customer_id == customer_id
        ).first()
        
        if not billing_account:
            return None
        
        # Get the most recent successful payment
        last_payment = db.query(Payment).filter(
            Payment.billing_account_id == billing_account.id,
            Payment.payment_status == 'completed'
        ).order_by(Payment.payment_date.desc()).first()
        
        return last_payment.payment_date if last_payment else None
    except Exception as e:
        logger.warning(f"Error getting last payment date for customer {customer_id}: {e}")
        return None
