"""
Billing System Service Layer

Comprehensive service layer for billing module with business logic for invoices,
payments, credit notes, and accounting for ISP Framework.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.billing import (
    CreditNote,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Payment,
    PaymentStatus,
)
from ..repositories.billing import (
    BillingManagementRepository,
    CreditNoteRepository,
    InvoiceItemRepository,
    InvoiceRepository,
    PaymentRepository,
    TaxRateRepository,
)
from ..schemas.billing import (
    CreditNoteCreate,
    CreditNoteSearch,
    InvoiceCreate,
    InvoiceItemCreate,
    InvoiceSearch,
    InvoiceUpdate,
    PaymentCreate,
    PaymentSearch,
)

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for invoice management"""

    def __init__(self, db: Session):
        self.db = db
        self.invoice_repo = InvoiceRepository(db)
        self.invoice_item_repo = InvoiceItemRepository(db)
        self.tax_rate_repo = TaxRateRepository(db)

    def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        """Create a new invoice with items"""
        try:
            # Generate invoice number
            invoice_number = self._generate_invoice_number()

            # Prepare invoice data
            invoice_dict = invoice_data.dict(exclude={"items"})
            invoice_dict["invoice_number"] = invoice_number
            invoice_dict["status"] = InvoiceStatus.DRAFT

            # Create invoice
            invoice = self.invoice_repo.create(invoice_dict)
            logger.info(
                f"Created invoice {invoice.invoice_number} for customer {invoice.customer_id}"
            )

            # Create invoice items
            if invoice_data.items:
                for item_data in invoice_data.items:
                    self._create_invoice_item(invoice.id, item_data)

            # Calculate and update totals
            self._calculate_and_update_totals(invoice.id)

            # Refresh invoice with items
            self.db.refresh(invoice)
            return invoice

        except Exception as e:
            logger.error(f"Error creating invoice: {str(e)}")
            self.db.rollback()
            raise

    def update_invoice(
        self, invoice_id: int, invoice_data: InvoiceUpdate
    ) -> Optional[Invoice]:
        """Update an existing invoice"""
        try:
            invoice = self.invoice_repo.get(invoice_id)
            if not invoice:
                return None

            # Only allow updates to draft invoices
            if invoice.status != InvoiceStatus.DRAFT:
                raise ValueError("Can only update draft invoices")

            # Update invoice
            update_dict = invoice_data.dict(exclude_unset=True)
            updated_invoice = self.invoice_repo.update(invoice_id, update_dict)

            # Recalculate totals if needed
            self._calculate_and_update_totals(invoice_id)

            logger.info(f"Updated invoice {updated_invoice.invoice_number}")
            return updated_invoice

        except Exception as e:
            logger.error(f"Error updating invoice {invoice_id}: {str(e)}")
            self.db.rollback()
            raise

    def search_invoices(self, search_params: InvoiceSearch) -> List[Invoice]:
        """Search invoices with filters"""
        try:
            search_dict = search_params.dict(exclude_unset=True)
            return self.invoice_repo.search_invoices(search_dict)
        except Exception as e:
            logger.error(f"Error searching invoices: {str(e)}")
            raise

    def get_customer_invoices(
        self, customer_id: int, limit: int = 100, offset: int = 0
    ) -> List[Invoice]:
        """Get invoices for a customer"""
        try:
            return self.invoice_repo.get_customer_invoices(customer_id, limit, offset)
        except Exception as e:
            logger.error(f"Error getting customer invoices: {str(e)}")
            raise

    def get_overdue_invoices(self) -> List[Invoice]:
        """Get all overdue invoices"""
        try:
            return self.invoice_repo.get_overdue_invoices()
        except Exception as e:
            logger.error(f"Error getting overdue invoices: {str(e)}")
            raise

    def get_billing_statistics(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get billing statistics for a date range"""
        try:
            return self.invoice_repo.get_billing_statistics(start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting billing statistics: {str(e)}")
            raise

    def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID"""
        return self.invoice_repo.get(invoice_id)

    def add_invoice_item(
        self, invoice_id: int, item_data: InvoiceItemCreate
    ) -> InvoiceItem:
        """Add an item to an existing invoice"""
        item = self._create_invoice_item(invoice_id, item_data)
        self._calculate_and_update_totals(invoice_id)
        return item

    def _create_invoice_item(
        self, invoice_id: int, item_data: InvoiceItemCreate
    ) -> InvoiceItem:
        """Create an invoice item with calculations"""
        item_dict = item_data.dict()
        item_dict["invoice_id"] = invoice_id

        # Calculate line total
        quantity = item_dict["quantity"]
        unit_price = item_dict["unit_price"]
        discount_amount = item_dict.get("discount_amount", Decimal("0"))
        discount_percentage = item_dict.get("discount_percentage", Decimal("0"))

        # Apply percentage discount if specified
        if discount_percentage > 0:
            discount_amount = unit_price * quantity * discount_percentage / 100
            item_dict["discount_amount"] = discount_amount

        # Calculate line total before tax
        line_total_before_tax = (unit_price * quantity) - discount_amount

        # Calculate tax
        tax_rate = item_dict.get("tax_rate", Decimal("0"))
        tax_amount = Decimal("0")
        if item_dict.get("taxable", True) and tax_rate > 0:
            tax_amount = line_total_before_tax * tax_rate / 100

        item_dict["tax_amount"] = tax_amount
        item_dict["line_total"] = line_total_before_tax + tax_amount

        return self.invoice_item_repo.create(item_dict)

    def _calculate_and_update_totals(self, invoice_id: int):
        """Calculate and update invoice totals"""
        totals = self.invoice_item_repo.calculate_invoice_totals(invoice_id)

        # Update invoice with calculated totals
        self.invoice_repo.update(
            invoice_id,
            {
                "subtotal": totals["subtotal"],
                "tax_amount": totals["tax_amount"],
                "discount_amount": totals["discount_amount"],
                "total_amount": totals["total_amount"],
                "balance_due": totals[
                    "total_amount"
                ],  # Initially, balance due equals total
            },
        )

    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        # Simple implementation - can be enhanced with custom formats
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month

        # Count invoices this month
        start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
        end_of_month = (
            datetime(year, month + 1, 1, tzinfo=timezone.utc)
            if month < 12
            else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        )

        monthly_count = (
            self.db.query(Invoice)
            .filter(
                Invoice.invoice_date >= start_of_month,
                Invoice.invoice_date < end_of_month,
            )
            .count()
        )

        return f"INV-{year:04d}{month:02d}-{monthly_count + 1:04d}"


class PaymentService:
    """Service for payment management"""

    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.invoice_repo = InvoiceRepository(db)

    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment"""
        try:
            # Validate invoice exists and is not fully paid
            invoice = self.invoice_repo.get(payment_data.invoice_id)
            if not invoice:
                raise ValueError("Invoice not found")

            if invoice.balance_due <= 0:
                raise ValueError("Invoice is already fully paid")

            if payment_data.amount > invoice.balance_due:
                raise ValueError("Payment amount exceeds balance due")

            # Generate payment number
            payment_number = self._generate_payment_number()

            # Prepare payment data
            payment_dict = payment_data.dict()
            payment_dict["payment_number"] = payment_number
            payment_dict["status"] = PaymentStatus.PENDING
            payment_dict["net_amount"] = payment_dict["amount"] - payment_dict.get(
                "processing_fee", Decimal("0")
            )

            # Create payment
            payment = self.payment_repo.create(payment_dict)

            # Process payment (mark as completed for now)
            self._process_payment(payment.id)

            logger.info(
                f"Created payment {payment.payment_number} for invoice {invoice.invoice_number}"
            )
            return payment

        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            self.db.rollback()
            raise

    def search_payments(self, search_params: PaymentSearch) -> List[Payment]:
        """Search payments with filters"""
        try:
            search_dict = search_params.dict(exclude_unset=True)
            return self.payment_repo.search_payments(search_dict)
        except Exception as e:
            logger.error(f"Error searching payments: {str(e)}")
            raise

    def _process_payment(self, payment_id: int) -> Optional[Payment]:
        """Internal method to process a payment"""
        payment = self.payment_repo.get(payment_id)
        if not payment:
            return None

        # Update payment status
        updated_payment = self.payment_repo.update(
            payment_id,
            {
                "status": PaymentStatus.COMPLETED,
                "processed_date": datetime.now(timezone.utc),
            },
        )

        # Update invoice balance
        invoice = self.invoice_repo.get(payment.invoice_id)
        new_paid_amount = invoice.paid_amount + payment.amount
        new_balance_due = invoice.total_amount - new_paid_amount

        # Update invoice status if fully paid
        invoice_update = {
            "paid_amount": new_paid_amount,
            "balance_due": new_balance_due,
        }

        if new_balance_due <= 0:
            invoice_update["status"] = InvoiceStatus.PAID
            invoice_update["paid_date"] = datetime.now(timezone.utc)

        self.invoice_repo.update(payment.invoice_id, invoice_update)

        return updated_payment

    def _generate_payment_number(self) -> str:
        """Generate unique payment number"""
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month

        # Count payments this month
        start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
        end_of_month = (
            datetime(year, month + 1, 1, tzinfo=timezone.utc)
            if month < 12
            else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        )

        monthly_count = (
            self.db.query(Payment)
            .filter(
                Payment.payment_date >= start_of_month,
                Payment.payment_date < end_of_month,
            )
            .count()
        )

        return f"PAY-{year:04d}{month:02d}-{monthly_count + 1:04d}"


class CreditNoteService:
    """Service for credit note management"""

    def __init__(self, db: Session):
        self.db = db
        self.credit_note_repo = CreditNoteRepository(db)
        self.invoice_repo = InvoiceRepository(db)

    def create_credit_note(self, credit_note_data: CreditNoteCreate) -> CreditNote:
        """Create a new credit note"""
        try:
            # Validate invoice exists
            invoice = self.invoice_repo.get(credit_note_data.invoice_id)
            if not invoice:
                raise ValueError("Invoice not found")

            # Generate credit note number
            credit_note_number = self._generate_credit_note_number()

            # Prepare credit note data
            credit_note_dict = credit_note_data.dict()
            credit_note_dict["credit_note_number"] = credit_note_number
            credit_note_dict["status"] = "active"

            # Create credit note
            credit_note = self.credit_note_repo.create(credit_note_dict)

            # Apply credit note to invoice
            self._apply_credit_note(credit_note.id)

            logger.info(
                f"Created credit note {credit_note.credit_note_number} for invoice {invoice.invoice_number}"
            )
            return credit_note

        except Exception as e:
            logger.error(f"Error creating credit note: {str(e)}")
            self.db.rollback()
            raise

    def search_credit_notes(self, search_params: CreditNoteSearch) -> List[CreditNote]:
        """Search credit notes with filters"""
        try:
            search_dict = search_params.dict(exclude_unset=True)
            return self.credit_note_repo.search_credit_notes(search_dict)
        except Exception as e:
            logger.error(f"Error searching credit notes: {str(e)}")
            raise

    def _apply_credit_note(self, credit_note_id: int) -> Optional[CreditNote]:
        """Internal method to apply a credit note"""
        credit_note = self.credit_note_repo.get(credit_note_id)
        if not credit_note:
            return None

        if credit_note.status != "active":
            raise ValueError("Credit note is not active")

        # Update credit note status
        updated_credit_note = self.credit_note_repo.update(
            credit_note_id,
            {"status": "applied", "applied_date": datetime.now(timezone.utc)},
        )

        # Update invoice balance
        invoice = self.invoice_repo.get(credit_note.invoice_id)
        new_balance_due = max(Decimal("0"), invoice.balance_due - credit_note.amount)

        invoice_update = {"balance_due": new_balance_due}

        # Update invoice status if balance is zero
        if new_balance_due <= 0 and invoice.status != InvoiceStatus.PAID:
            invoice_update["status"] = InvoiceStatus.PAID
            invoice_update["paid_date"] = datetime.now(timezone.utc)

        self.invoice_repo.update(credit_note.invoice_id, invoice_update)

        return updated_credit_note

    def _generate_credit_note_number(self) -> str:
        """Generate unique credit note number"""
        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month

        # Count credit notes this month
        start_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
        end_of_month = (
            datetime(year, month + 1, 1, tzinfo=timezone.utc)
            if month < 12
            else datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        )

        monthly_count = (
            self.db.query(CreditNote)
            .filter(
                CreditNote.credit_date >= start_of_month,
                CreditNote.credit_date < end_of_month,
            )
            .count()
        )

        return f"CN-{year:04d}{month:02d}-{monthly_count + 1:04d}"


class BillingManagementService:
    """Unified service for comprehensive billing management"""

    def __init__(self, db: Session):
        self.db = db
        self.billing_repo = BillingManagementRepository(db)
        self.invoice_service = InvoiceService(db)
        self.payment_service = PaymentService(db)
        self.credit_note_service = CreditNoteService(db)

    def get_billing_overview(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get comprehensive billing overview"""
        try:
            # Get basic statistics
            stats = self.invoice_service.get_billing_statistics(start_date, end_date)

            # Add additional metrics
            overdue_invoices = self.invoice_service.get_overdue_invoices()
            stats["overdue_invoices"] = len(overdue_invoices)

            # Calculate collection rate
            if stats["total_amount"] > 0:
                stats["collection_rate"] = float(
                    (stats["paid_amount"] / stats["total_amount"]) * 100
                )
            else:
                stats["collection_rate"] = 0.0

            return stats

        except Exception as e:
            logger.error(f"Error getting billing overview: {str(e)}")
            raise

    def get_customer_billing_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive billing summary for a customer"""
        try:
            return self.billing_repo.get_customer_billing_summary(customer_id)
        except Exception as e:
            logger.error(f"Error getting customer billing summary: {str(e)}")
            raise
