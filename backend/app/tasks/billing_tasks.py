"""
Billing and Financial Task Processing
Background tasks for billing operations, invoice generation, and payment processing
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import current_app
from sqlalchemy.orm import Session

from app.core.celery import celery_app
from app.core.database import get_db
from app.models.billing import Invoice, Payment, BillingCycle
from app.models.customers import Customer
from app.services.billing import BillingService
import structlog

logger = structlog.get_logger("isp.tasks.billing")


@celery_app.task(bind=True, name="billing.generate_invoices")
def generate_invoices_task(self, billing_cycle_id: int = None):
    """Generate invoices for customers based on billing cycles."""
    try:
        logger.info("Starting invoice generation", billing_cycle_id=billing_cycle_id)
        
        db = next(get_db())
        billing_service = BillingService(db)
        
        if billing_cycle_id:
            # Generate invoices for specific billing cycle
            result = billing_service.generate_invoices_for_cycle(billing_cycle_id)
        else:
            # Generate invoices for all due cycles
            result = billing_service.generate_due_invoices()
        
        logger.info("Invoice generation completed", 
                   invoices_generated=result.get('invoices_generated', 0),
                   total_amount=result.get('total_amount', 0))
        
        return {
            "status": "success",
            "invoices_generated": result.get('invoices_generated', 0),
            "total_amount": float(result.get('total_amount', 0)),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Invoice generation failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="billing.process_payments")
def process_payments_task(self, payment_batch_id: str = None):
    """Process pending payments and update account balances."""
    try:
        logger.info("Starting payment processing", batch_id=payment_batch_id)
        
        db = next(get_db())
        billing_service = BillingService(db)
        
        result = billing_service.process_pending_payments(payment_batch_id)
        
        logger.info("Payment processing completed",
                   payments_processed=result.get('payments_processed', 0),
                   total_amount=result.get('total_amount', 0))
        
        return {
            "status": "success",
            "payments_processed": result.get('payments_processed', 0),
            "total_amount": float(result.get('total_amount', 0)),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Payment processing failed", error=str(exc))
        raise self.retry(exc=exc, countdown=180, max_retries=5)


@celery_app.task(bind=True, name="billing.send_overdue_notices")
def send_overdue_notices_task(self, days_overdue: int = 30):
    """Send overdue payment notices to customers."""
    try:
        logger.info("Starting overdue notice generation", days_overdue=days_overdue)
        
        db = next(get_db())
        billing_service = BillingService(db)
        
        result = billing_service.send_overdue_notices(days_overdue)
        
        logger.info("Overdue notices sent",
                   notices_sent=result.get('notices_sent', 0))
        
        return {
            "status": "success",
            "notices_sent": result.get('notices_sent', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Overdue notice sending failed", error=str(exc))
        raise self.retry(exc=exc, countdown=600, max_retries=2)


@celery_app.task(bind=True, name="billing.calculate_usage_charges")
def calculate_usage_charges_task(self, customer_id: int = None, billing_period: str = None):
    """Calculate usage-based charges for services."""
    try:
        logger.info("Starting usage charge calculation", 
                   customer_id=customer_id, 
                   billing_period=billing_period)
        
        db = next(get_db())
        billing_service = BillingService(db)
        
        if customer_id:
            result = billing_service.calculate_customer_usage_charges(customer_id, billing_period)
        else:
            result = billing_service.calculate_all_usage_charges(billing_period)
        
        logger.info("Usage charge calculation completed",
                   charges_calculated=result.get('charges_calculated', 0),
                   total_amount=result.get('total_amount', 0))
        
        return {
            "status": "success",
            "charges_calculated": result.get('charges_calculated', 0),
            "total_amount": float(result.get('total_amount', 0)),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Usage charge calculation failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=3)


@celery_app.task(bind=True, name="billing.reconcile_accounts")
def reconcile_accounts_task(self, account_ids: List[int] = None):
    """Reconcile customer account balances and transactions."""
    try:
        logger.info("Starting account reconciliation", account_count=len(account_ids) if account_ids else "all")
        
        db = next(get_db())
        billing_service = BillingService(db)
        
        result = billing_service.reconcile_accounts(account_ids)
        
        logger.info("Account reconciliation completed",
                   accounts_reconciled=result.get('accounts_reconciled', 0),
                   discrepancies_found=result.get('discrepancies_found', 0))
        
        return {
            "status": "success",
            "accounts_reconciled": result.get('accounts_reconciled', 0),
            "discrepancies_found": result.get('discrepancies_found', 0),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Account reconciliation failed", error=str(exc))
        raise self.retry(exc=exc, countdown=600, max_retries=2)


# Scheduled tasks
@celery_app.task(bind=True, name="billing.daily_billing_tasks")
def daily_billing_tasks(self):
    """Run daily billing maintenance tasks."""
    try:
        logger.info("Starting daily billing tasks")
        
        results = {}
        
        # Generate due invoices
        invoice_result = generate_invoices_task.delay()
        results['invoice_generation'] = invoice_result.id
        
        # Process pending payments
        payment_result = process_payments_task.delay()
        results['payment_processing'] = payment_result.id
        
        # Calculate usage charges
        usage_result = calculate_usage_charges_task.delay()
        results['usage_calculation'] = usage_result.id
        
        logger.info("Daily billing tasks scheduled", task_ids=results)
        
        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Daily billing tasks failed", error=str(exc))
        raise self.retry(exc=exc, countdown=1800, max_retries=2)


@celery_app.task(bind=True, name="billing.monthly_billing_tasks")
def monthly_billing_tasks(self):
    """Run monthly billing maintenance tasks."""
    try:
        logger.info("Starting monthly billing tasks")
        
        results = {}
        
        # Send overdue notices
        overdue_result = send_overdue_notices_task.delay(30)
        results['overdue_notices'] = overdue_result.id
        
        # Reconcile all accounts
        reconcile_result = reconcile_accounts_task.delay()
        results['account_reconciliation'] = reconcile_result.id
        
        logger.info("Monthly billing tasks scheduled", task_ids=results)
        
        return {
            "status": "success",
            "scheduled_tasks": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Monthly billing tasks failed", error=str(exc))
        raise self.retry(exc=exc, countdown=3600, max_retries=2)
