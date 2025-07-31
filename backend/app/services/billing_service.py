"""
Billing Service Layer

Comprehensive service layer for the modular billing system with advanced ISP-specific features:
- Real-time balance management
- Hybrid prepaid/postpaid billing
- Automated invoice generation
- Payment processing and gateway integration
- Credit note management
- Payment plan handling
- Dunning management
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from app.models.billing import (
    AccountStatus,
    BalanceHistory,
    BillingTransaction,
    BillingType,
    CustomerBillingAccount,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentMethodType,
    PaymentStatus,
    TransactionCategory,
    TransactionType,
)
from app.services.webhook_integration_service import WebhookTriggers

logger = logging.getLogger(__name__)


class BillingAccountService:
    """Service for managing customer billing accounts"""

    def __init__(self, db: Session):
        self.db = db

    def create_billing_account(
        self, customer_id: int, billing_type: BillingType, account_data: Dict[str, Any]
    ) -> CustomerBillingAccount:
        """Create a new billing account for a customer"""
        try:
            # Generate unique account number
            account_number = self._generate_account_number(customer_id)

            # Create billing account
            billing_account = CustomerBillingAccount(
                customer_id=customer_id,
                account_number=account_number,
                billing_type=billing_type,
                account_status=AccountStatus.ACTIVE,
                available_balance=Decimal("0.00"),
                reserved_balance=Decimal("0.00"),
                **account_data,
            )

            self.db.add(billing_account)
            self.db.commit()
            self.db.refresh(billing_account)

            logger.info(
                f"Created billing account {account_number} for customer {customer_id}"
            )
            return billing_account

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating billing account: {e}")
            raise BusinessLogicError(f"Failed to create billing account: {str(e)}")

    def get_account_balance(self, account_id: int) -> Dict[str, Decimal]:
        """Get current account balance information"""
        account = self._get_account(account_id)

        return {
            "available_balance": account.available_balance or Decimal("0.00"),
            "reserved_balance": account.reserved_balance or Decimal("0.00"),
            "total_balance": (account.available_balance or Decimal("0.00"))
            + (account.reserved_balance or Decimal("0.00")),
            "credit_limit": account.credit_limit or Decimal("0.00"),
        }

    def update_balance(
        self,
        account_id: int,
        amount: Decimal,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[int] = None,
    ) -> BillingTransaction:
        """Update account balance with transaction logging"""
        try:
            account = self._get_account(account_id)

            # Record balance before change
            balance_before = account.available_balance or Decimal("0.00")

            # Apply balance change
            if transaction_type in [TransactionType.CREDIT, TransactionType.PAYMENT]:
                account.available_balance = balance_before + amount
            elif transaction_type in [TransactionType.DEBIT, TransactionType.CHARGE]:
                account.available_balance = balance_before - amount

            balance_after = account.available_balance

            # Create transaction record
            transaction = BillingTransaction(
                transaction_id=self._generate_transaction_id(),
                billing_account_id=account_id,
                transaction_type=transaction_type,
                transaction_category=self._get_transaction_category(transaction_type),
                amount=amount,
                currency=account.currency or "USD",
                description=description,
                reference_id=reference_id,
                effective_date=datetime.now(timezone.utc),
            )

            # Create balance history record
            balance_history = BalanceHistory(
                billing_account_id=account_id,
                balance_before=balance_before,
                balance_after=balance_after,
                change_amount=balance_after - balance_before,
                change_reason=description,
                snapshot_date=datetime.now(timezone.utc),
            )

            self.db.add(transaction)
            self.db.add(balance_history)
            self.db.commit()
            self.db.refresh(transaction)

            logger.info(
                f"Updated balance for account {account_id}: {balance_before} -> {balance_after}"
            )
            return transaction

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating balance: {e}")
            raise BusinessLogicError(f"Failed to update balance: {str(e)}")

    def _get_account(self, account_id: int) -> CustomerBillingAccount:
        """Get billing account by ID"""
        account = (
            self.db.query(CustomerBillingAccount)
            .filter(CustomerBillingAccount.id == account_id)
            .first()
        )

        if not account:
            raise NotFoundError(f"Billing account {account_id} not found")

        return account

    def _generate_account_number(self, customer_id: int) -> str:
        """Generate unique account number"""
        return f"BA{customer_id:06d}{datetime.now().strftime('%Y%m')}"

    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{datetime.now().microsecond:06d}"

    def _get_transaction_category(
        self, transaction_type: TransactionType
    ) -> TransactionCategory:
        """Map transaction type to category"""
        mapping = {
            TransactionType.PAYMENT: TransactionCategory.PAYMENT,
            TransactionType.CHARGE: TransactionCategory.SERVICE_FEE,
            TransactionType.REFUND: TransactionCategory.REFUND,
            TransactionType.ADJUSTMENT: TransactionCategory.ADJUSTMENT,
        }
        return mapping.get(transaction_type, TransactionCategory.ADJUSTMENT)


class InvoiceService:
    """Service for managing invoices and invoice items"""

    def __init__(self, db: Session):
        self.db = db

    def create_invoice(
        self,
        billing_account_id: int,
        invoice_data: Dict[str, Any],
        invoice_items: List[Dict[str, Any]],
    ) -> Invoice:
        """Create a new invoice with items"""
        try:
            # Generate invoice number
            invoice_number = self._generate_invoice_number()

            # Calculate totals from items
            subtotal = sum(
                Decimal(str(item.get("line_total", 0))) for item in invoice_items
            )
            tax_amount = sum(
                Decimal(str(item.get("tax_amount", 0))) for item in invoice_items
            )
            discount_amount = sum(
                Decimal(str(item.get("discount_amount", 0))) for item in invoice_items
            )
            subtotal + tax_amount - discount_amount

            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                billing_account_id=billing_account_id,
                invoice_status=InvoiceStatus.DRAFT,
                invoice_date=datetime.now(timezone.utc),
                due_date=invoice_data.get("due_date", datetime.now(timezone.utc)),
            )
            self.db.add(invoice)
            self.db.flush()

            # Create invoice items
            for item_data in invoice_items:
                invoice_item = InvoiceItem(invoice_id=invoice.id, **item_data)
                self.db.add(invoice_item)

            self.db.commit()

            # Trigger webhook event
            try:
                self.webhook_triggers.invoice_created(
                    {
                        "id": invoice.id,
                        "customer_id": invoice.billing_account.customer_id,
                        "invoice_number": invoice.invoice_number,
                        "total_amount": float(invoice.total_amount),
                        "due_date": invoice.due_date.isoformat(),
                        "status": invoice.status.value,
                        "items": [
                            {
                                "description": item.description,
                                "quantity": float(item.quantity),
                                "unit_price": float(item.unit_price),
                                "total_price": float(item.total_price),
                            }
                            for item in invoice.invoice_items
                        ],
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to trigger invoice.created webhook: {e}")

            logger.info(
                f"Created invoice {invoice_number} for account {billing_account_id}"
            )
            return invoice

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating invoice: {e}")
            raise BusinessLogicError(f"Failed to create invoice: {str(e)}")

    def finalize_invoice(self, invoice_id: int) -> Invoice:
        """Finalize invoice and make it ready for payment"""
        try:
            invoice = self._get_invoice(invoice_id)

            if invoice.invoice_status != InvoiceStatus.DRAFT:
                raise ValidationError("Only draft invoices can be finalized")

            invoice.invoice_status = InvoiceStatus.PENDING
            invoice.sent_date = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(invoice)

            logger.info(f"Finalized invoice {invoice.invoice_number}")
            return invoice

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error finalizing invoice: {e}")
            raise BusinessLogicError(f"Failed to finalize invoice: {str(e)}")

    def apply_proration(
        self,
        invoice_item: InvoiceItem,
        service_period_start: datetime,
        service_period_end: datetime,
        billing_period_start: datetime,
        billing_period_end: datetime,
    ) -> InvoiceItem:
        """Apply proration to invoice item based on service period"""
        try:
            # Calculate proration factor
            total_days = (billing_period_end - billing_period_start).days
            service_days = (service_period_end - service_period_start).days

            if total_days <= 0:
                proration_factor = Decimal("1.0000")
            else:
                proration_factor = Decimal(str(service_days / total_days))

            # Apply proration
            original_amount = invoice_item.unit_price * invoice_item.quantity
            prorated_amount = original_amount * proration_factor

            invoice_item.proration_factor = proration_factor
            invoice_item.line_total = prorated_amount
            invoice_item.service_period_start = service_period_start
            invoice_item.service_period_end = service_period_end

            self.db.commit()

            logger.info(
                f"Applied proration factor {proration_factor} to invoice item {invoice_item.id}"
            )
            return invoice_item

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error applying proration: {e}")
            raise BusinessLogicError(f"Failed to apply proration: {str(e)}")

    def _get_invoice(self, invoice_id: int) -> Invoice:
        """Get invoice by ID"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise NotFoundError(f"Invoice {invoice_id} not found")

        return invoice

    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        return f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"


class PaymentService:
    """Service for managing payments and payment methods"""

    def __init__(self, db: Session, webhook_triggers: WebhookTriggers):
        self.db = db
        self.webhook_triggers = webhook_triggers

    def process_payment(
        self,
        billing_account_id: int,
        amount: Decimal,
        payment_method_id: int,
        invoice_id: Optional[int] = None,
        payment_data: Optional[Dict[str, Any]] = None,
    ) -> Payment:
        """Process a payment for a billing account"""
        try:
            # Generate payment reference
            payment_reference = self._generate_payment_reference()

            # Create payment record
            payment = Payment(
                payment_reference=payment_reference,
                billing_account_id=billing_account_id,
                invoice_id=invoice_id,
                payment_method_id=payment_method_id,
                payment_status=PaymentStatus.PENDING,
                amount=amount,
                currency=payment_data.get("currency", "USD") if payment_data else "USD",
                payment_date=datetime.now(timezone.utc),
                **(payment_data or {}),
            )

            self.db.add(payment)
            self.db.flush()  # Get payment ID

            # Update account balance
            billing_service = BillingAccountService(self.db)
            billing_service.update_balance(
                account_id=billing_account_id,
                amount=amount,
                transaction_type=TransactionType.PAYMENT,
                description=f"Payment {payment_reference}",
                reference_id=payment.id,
            )

            # Update payment status
            payment.payment_status = PaymentStatus.COMPLETED

            # Update invoice if provided
            if invoice_id:
                self._update_invoice_payment_status(invoice_id, amount)

            self.db.commit()
            self.db.refresh(payment)

            # Trigger webhook event
            try:
                self.webhook_triggers.invoice_paid(
                    {
                        "id": invoice_id,
                        "customer_id": payment.billing_account.customer_id,
                        "invoice_number": payment.invoice.invoice_number,
                        "total_amount": float(payment.invoice.total_amount),
                        "paid_amount": float(payment.amount),
                        "payment_method": payment.payment_method.type.value,
                        "paid_at": payment.payment_date.isoformat(),
                    },
                    {
                        "amount": float(payment.amount),
                        "payment_method": payment.payment_method.type.value,
                        "paid_at": payment.payment_date.isoformat(),
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to trigger invoice.paid webhook: {e}")

            logger.info(f"Processed payment {payment_reference} for amount {amount}")
            return payment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing payment: {e}")
            raise BusinessLogicError(f"Failed to process payment: {str(e)}")

    def create_payment_method(
        self,
        billing_account_id: int,
        method_type: PaymentMethodType,
        method_data: Dict[str, Any],
    ) -> PaymentMethod:
        """Create a new payment method for a billing account"""
        try:
            payment_method = PaymentMethod(
                billing_account_id=billing_account_id,
                method_type=method_type,
                is_active=True,
                **method_data,
            )

            self.db.add(payment_method)
            self.db.commit()
            self.db.refresh(payment_method)

            logger.info(
                f"Created payment method {method_type} for billing account {billing_account_id}"
            )
            return payment_method

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating payment method: {e}")
            raise BusinessLogicError(f"Failed to create payment method: {str(e)}")

    def _update_invoice_payment_status(self, invoice_id: int, payment_amount: Decimal):
        """Update invoice payment status based on payment amount"""
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if invoice and payment_amount >= invoice.total_amount:
            invoice.invoice_status = InvoiceStatus.PAID
            invoice.paid_at = datetime.now(timezone.utc)
            invoice.updated_at = datetime.now(timezone.utc)

    def _generate_payment_reference(self) -> str:
        """Generate unique payment reference"""
        return f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{datetime.now().microsecond:06d}"


class BillingReportService:
    """Service for generating billing reports and analytics"""

    def __init__(self, db: Session):
        self.db = db

    def get_account_summary(self, account_id: int) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        account = (
            self.db.query(CustomerBillingAccount)
            .filter(CustomerBillingAccount.id == account_id)
            .first()
        )

        if not account:
            raise NotFoundError(f"Billing account {account_id} not found")

        # Get transaction summary
        transactions = (
            self.db.query(BillingTransaction)
            .filter(BillingTransaction.billing_account_id == account_id)
            .all()
        )

        # Get invoice summary
        invoices = (
            self.db.query(Invoice)
            .filter(Invoice.billing_account_id == account_id)
            .all()
        )

        # Get payment summary
        payments = (
            self.db.query(Payment)
            .filter(Payment.billing_account_id == account_id)
            .all()
        )

        return {
            "account_info": {
                "account_number": account.account_number,
                "billing_type": account.billing_type,
                "account_status": account.account_status,
                "available_balance": account.available_balance,
                "reserved_balance": account.reserved_balance,
                "credit_limit": account.credit_limit,
            },
            "transaction_summary": {
                "total_transactions": len(transactions),
                "total_credits": sum(
                    t.amount
                    for t in transactions
                    if t.transaction_type
                    in [TransactionType.CREDIT, TransactionType.PAYMENT]
                ),
                "total_debits": sum(
                    t.amount
                    for t in transactions
                    if t.transaction_type
                    in [TransactionType.DEBIT, TransactionType.CHARGE]
                ),
            },
            "invoice_summary": {
                "total_invoices": len(invoices),
                "total_amount": sum(i.total_amount for i in invoices),
                "paid_invoices": len(
                    [i for i in invoices if i.invoice_status == InvoiceStatus.PAID]
                ),
                "overdue_invoices": len(
                    [i for i in invoices if i.invoice_status == InvoiceStatus.OVERDUE]
                ),
            },
            "payment_summary": {
                "total_payments": len(payments),
                "total_amount": sum(
                    p.amount
                    for p in payments
                    if p.payment_status == PaymentStatus.COMPLETED
                ),
                "successful_payments": len(
                    [p for p in payments if p.payment_status == PaymentStatus.COMPLETED]
                ),
                "failed_payments": len(
                    [p for p in payments if p.payment_status == PaymentStatus.FAILED]
                ),
            },
        }


# Service factory for dependency injection
def get_billing_account_service(db: Session) -> BillingAccountService:
    return BillingAccountService(db)


def get_invoice_service(db: Session) -> InvoiceService:
    return InvoiceService(db)


def get_payment_service(db: Session) -> PaymentService:
    return PaymentService(db)


def get_billing_report_service(db: Session) -> BillingReportService:
    return BillingReportService(db)
