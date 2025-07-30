"""
Billing Automation Service

Service layer for automated billing processes including:
- Recurring invoice generation
- Proration calculations for mid-cycle changes
- Payment retry logic and dunning sequences
- Commission calculations for resellers
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.core.exceptions import NotFoundError, ValidationError
from app.services.webhook_integration_service import WebhookTriggers
import logging

logger = logging.getLogger(__name__)


class BillingAutomationService:
    """Service layer for billing automation and lifecycle management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
    
    def generate_recurring_invoices(self, billing_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate recurring invoices for services due for billing."""
        if not billing_date:
            billing_date = datetime.now(timezone.utc).date()
        
        try:
            # Get all services due for billing
            services_due = self._get_services_due_for_billing(billing_date)
            
            invoices_created = 0
            total_amount = Decimal('0.00')
            errors = []
            
            for service in services_due:
                try:
                    invoice = self._create_service_invoice(service, billing_date)
                    invoices_created += 1
                    total_amount += invoice['amount']
                    
                    # Trigger webhook for invoice creation
                    self.webhook_triggers.invoice_created({
                        'invoice_id': invoice['id'],
                        'customer_id': service['customer_id'],
                        'service_id': service['id'],
                        'amount': float(invoice['amount']),
                        'due_date': invoice['due_date'].isoformat(),
                        'billing_period': invoice['billing_period']
                    })
                    
                except Exception as e:
                    logger.error(f"Error creating invoice for service {service['id']}: {e}")
                    errors.append({
                        'service_id': service['id'],
                        'customer_id': service['customer_id'],
                        'error': str(e)
                    })
            
            logger.info(f"Generated {invoices_created} recurring invoices totaling ${total_amount}")
            
            return {
                'invoices_created': invoices_created,
                'total_amount': float(total_amount),
                'billing_date': billing_date.isoformat(),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error in recurring invoice generation: {e}")
            raise
    
    def calculate_proration(
        self, 
        service_id: int, 
        change_type: str,  # 'activation', 'suspension', 'termination', 'upgrade', 'downgrade'
        change_date: datetime,
        old_amount: Optional[Decimal] = None,
        new_amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Calculate proration for mid-cycle service changes."""
        try:
            # Get service billing information
            service = self._get_service_billing_info(service_id)
            
            # Get current billing cycle
            cycle_start, cycle_end = self._get_current_billing_cycle(service)
            
            # Calculate proration based on change type
            if change_type == 'activation':
                proration = self._calculate_activation_proration(
                    service['monthly_fee'], change_date, cycle_start, cycle_end
                )
            elif change_type == 'suspension':
                proration = self._calculate_suspension_proration(
                    service['monthly_fee'], change_date, cycle_start, cycle_end
                )
            elif change_type == 'termination':
                proration = self._calculate_termination_proration(
                    service['monthly_fee'], change_date, cycle_start, cycle_end
                )
            elif change_type in ['upgrade', 'downgrade']:
                proration = self._calculate_plan_change_proration(
                    old_amount, new_amount, change_date, cycle_start, cycle_end
                )
            else:
                raise ValidationError(f"Unknown change type: {change_type}")
            
            logger.info(f"Calculated proration for service {service_id}: {proration}")
            return proration
            
        except Exception as e:
            logger.error(f"Error calculating proration for service {service_id}: {e}")
            raise
    
    def process_payment_retries(self) -> Dict[str, Any]:
        """Process payment retries for failed payments."""
        try:
            # Get failed payments eligible for retry
            failed_payments = self._get_failed_payments_for_retry()
            
            retries_processed = 0
            successful_retries = 0
            failed_retries = 0
            
            for payment in failed_payments:
                try:
                    # Attempt payment retry
                    retry_result = self._retry_payment(payment)
                    retries_processed += 1
                    
                    if retry_result['success']:
                        successful_retries += 1
                        
                        # Trigger webhook for successful payment
                        self.webhook_triggers.payment_succeeded({
                            'payment_id': payment['id'],
                            'invoice_id': payment['invoice_id'],
                            'customer_id': payment['customer_id'],
                            'amount': float(payment['amount']),
                            'retry_attempt': payment['retry_count'] + 1
                        })
                    else:
                        failed_retries += 1
                        
                        # Check if max retries reached
                        if payment['retry_count'] >= payment['max_retries']:
                            self._initiate_dunning_process(payment)
                        
                        # Trigger webhook for failed payment
                        self.webhook_triggers.payment_failed({
                            'payment_id': payment['id'],
                            'invoice_id': payment['invoice_id'],
                            'customer_id': payment['customer_id'],
                            'amount': float(payment['amount']),
                            'retry_attempt': payment['retry_count'] + 1,
                            'reason': retry_result.get('error_message')
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing payment retry {payment['id']}: {e}")
                    failed_retries += 1
            
            logger.info(f"Processed {retries_processed} payment retries: {successful_retries} successful, {failed_retries} failed")
            
            return {
                'retries_processed': retries_processed,
                'successful_retries': successful_retries,
                'failed_retries': failed_retries
            }
            
        except Exception as e:
            logger.error(f"Error processing payment retries: {e}")
            raise
    
    def calculate_reseller_commission(self, reseller_id: int, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Calculate commission for a reseller for a given period."""
        try:
            # Get reseller commission structure
            commission_structure = self._get_reseller_commission_structure(reseller_id)
            
            # Get reseller's customer payments for the period
            payments = self._get_reseller_payments(reseller_id, period_start, period_end)
            
            total_revenue = Decimal('0.00')
            total_commission = Decimal('0.00')
            service_commissions = {}
            
            for payment in payments:
                service_type = payment['service_type']
                amount = Decimal(str(payment['amount']))
                
                # Calculate commission based on service type
                commission_rate = commission_structure.get(service_type, commission_structure.get('default', 0.10))
                commission = amount * Decimal(str(commission_rate))
                
                total_revenue += amount
                total_commission += commission
                
                if service_type not in service_commissions:
                    service_commissions[service_type] = {
                        'revenue': Decimal('0.00'),
                        'commission': Decimal('0.00'),
                        'rate': commission_rate
                    }
                
                service_commissions[service_type]['revenue'] += amount
                service_commissions[service_type]['commission'] += commission
            
            # Create commission record
            commission_record = self._create_commission_record(
                reseller_id, period_start, period_end, total_revenue, total_commission, service_commissions
            )
            
            logger.info(f"Calculated commission for reseller {reseller_id}: ${total_commission} on ${total_revenue} revenue")
            
            return {
                'reseller_id': reseller_id,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'total_revenue': float(total_revenue),
                'total_commission': float(total_commission),
                'commission_rate': float(total_commission / total_revenue) if total_revenue > 0 else 0,
                'service_breakdown': {
                    k: {
                        'revenue': float(v['revenue']),
                        'commission': float(v['commission']),
                        'rate': v['rate']
                    } for k, v in service_commissions.items()
                },
                'commission_record_id': commission_record['id']
            }
            
        except Exception as e:
            logger.error(f"Error calculating reseller commission: {e}")
            raise
    
    def _get_services_due_for_billing(self, billing_date: datetime.date) -> List[Dict[str, Any]]:
        """Get services that are due for billing on the specified date."""
        # Placeholder - implement when service repository is available
        # This would query active services where next_billing_date <= billing_date
        return []
    
    def _create_service_invoice(self, service: Dict[str, Any], billing_date: datetime.date) -> Dict[str, Any]:
        """Create an invoice for a service."""
        # Placeholder - implement when invoice repository is available
        invoice_data = {
            'id': f"inv_{service['id']}_{billing_date.strftime('%Y%m%d')}",
            'customer_id': service['customer_id'],
            'service_id': service['id'],
            'amount': Decimal(str(service['monthly_fee'])),
            'due_date': billing_date + timedelta(days=30),
            'billing_period': f"{billing_date.strftime('%Y-%m')}"
        }
        return invoice_data
    
    def _get_service_billing_info(self, service_id: int) -> Dict[str, Any]:
        """Get billing information for a service."""
        # Placeholder - implement when service repository is available
        return {
            'id': service_id,
            'customer_id': 1,
            'monthly_fee': 89.99,
            'billing_cycle': 'monthly',
            'next_billing_date': datetime.now(timezone.utc).date()
        }
    
    def _get_current_billing_cycle(self, service: Dict[str, Any]) -> tuple:
        """Get the current billing cycle start and end dates."""
        # Placeholder - implement billing cycle logic
        now = datetime.now(timezone.utc)
        cycle_start = now.replace(day=1)
        
        # Calculate next month
        if now.month == 12:
            cycle_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            cycle_end = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        
        return cycle_start, cycle_end
    
    def _calculate_activation_proration(self, monthly_fee: Decimal, activation_date: datetime, cycle_start: datetime, cycle_end: datetime) -> Dict[str, Any]:
        """Calculate proration for service activation."""
        total_days = (cycle_end - cycle_start).days + 1
        remaining_days = (cycle_end.date() - activation_date.date()).days + 1
        
        daily_rate = Decimal(str(monthly_fee)) / total_days
        prorated_amount = daily_rate * remaining_days
        
        return {
            'type': 'activation',
            'monthly_fee': float(monthly_fee),
            'total_days': total_days,
            'billable_days': remaining_days,
            'daily_rate': float(daily_rate),
            'prorated_amount': float(prorated_amount),
            'activation_date': activation_date.date().isoformat()
        }
    
    def _calculate_suspension_proration(self, monthly_fee: Decimal, suspension_date: datetime, cycle_start: datetime, cycle_end: datetime) -> Dict[str, Any]:
        """Calculate proration for service suspension."""
        total_days = (cycle_end - cycle_start).days + 1
        used_days = (suspension_date.date() - cycle_start.date()).days + 1
        
        daily_rate = Decimal(str(monthly_fee)) / total_days
        credit_amount = daily_rate * (total_days - used_days)
        
        return {
            'type': 'suspension',
            'monthly_fee': float(monthly_fee),
            'total_days': total_days,
            'used_days': used_days,
            'daily_rate': float(daily_rate),
            'credit_amount': float(credit_amount),
            'suspension_date': suspension_date.date().isoformat()
        }
    
    def _calculate_termination_proration(self, monthly_fee: Decimal, termination_date: datetime, cycle_start: datetime, cycle_end: datetime) -> Dict[str, Any]:
        """Calculate proration for service termination."""
        return self._calculate_suspension_proration(monthly_fee, termination_date, cycle_start, cycle_end)
    
    def _calculate_plan_change_proration(self, old_amount: Decimal, new_amount: Decimal, change_date: datetime, cycle_start: datetime, cycle_end: datetime) -> Dict[str, Any]:
        """Calculate proration for plan changes."""
        total_days = (cycle_end - cycle_start).days + 1
        remaining_days = (cycle_end.date() - change_date.date()).days + 1
        
        old_daily_rate = old_amount / total_days
        new_daily_rate = new_amount / total_days
        
        # Credit for old plan
        old_credit = old_daily_rate * remaining_days
        
        # Charge for new plan
        new_charge = new_daily_rate * remaining_days
        
        # Net adjustment
        net_adjustment = new_charge - old_credit
        
        return {
            'type': 'plan_change',
            'old_amount': float(old_amount),
            'new_amount': float(new_amount),
            'total_days': total_days,
            'remaining_days': remaining_days,
            'old_daily_rate': float(old_daily_rate),
            'new_daily_rate': float(new_daily_rate),
            'old_credit': float(old_credit),
            'new_charge': float(new_charge),
            'net_adjustment': float(net_adjustment),
            'change_date': change_date.date().isoformat()
        }
    
    def _get_failed_payments_for_retry(self) -> List[Dict[str, Any]]:
        """Get failed payments that are eligible for retry."""
        # Placeholder - implement when payment repository is available
        return []
    
    def _retry_payment(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to retry a failed payment."""
        # Placeholder - implement payment processing logic
        return {
            'success': False,
            'error_message': 'Payment gateway unavailable'
        }
    
    def _initiate_dunning_process(self, payment: Dict[str, Any]):
        """Initiate dunning process for repeatedly failed payments."""
        # Placeholder - implement dunning logic
        logger.info(f"Initiating dunning process for payment {payment['id']}")
    
    def _get_reseller_commission_structure(self, reseller_id: int) -> Dict[str, float]:
        """Get commission structure for a reseller."""
        # Placeholder - implement when reseller repository is available
        return {
            'internet': 0.15,
            'voice': 0.12,
            'bundle': 0.18,
            'default': 0.10
        }
    
    def _get_reseller_payments(self, reseller_id: int, period_start: datetime, period_end: datetime) -> List[Dict[str, Any]]:
        """Get payments for reseller's customers in the specified period."""
        # Placeholder - implement when payment repository is available
        return []
    
    def _create_commission_record(self, reseller_id: int, period_start: datetime, period_end: datetime, total_revenue: Decimal, total_commission: Decimal, service_commissions: Dict) -> Dict[str, Any]:
        """Create a commission record for a reseller."""
        # Placeholder - implement when commission repository is available
        return {
            'id': f"comm_{reseller_id}_{period_start.strftime('%Y%m%d')}",
            'reseller_id': reseller_id,
            'period_start': period_start,
            'period_end': period_end,
            'total_revenue': total_revenue,
            'total_commission': total_commission
        }
