"""
Billing System Repositories

Repository classes for billing module following the established repository pattern
for ISP Framework.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..models.billing import (
    AccountingEntry,
    BillingCycle,
    CreditNote,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Payment,
    PaymentRefund,
    TaxRate,
)
from .base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for invoice management"""

    def __init__(self, db: Session):
        super().__init__(Invoice, db)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        return (
            self.db.query(self.model)
            .filter(self.model.invoice_number == invoice_number)
            .first()
        )

    def get_customer_invoices(
        self, customer_id: int, limit: int = 100, offset: int = 0
    ) -> List[Invoice]:
        """Get invoices for a specific customer"""
        return self.get_all(
            filters={"customer_id": customer_id},
            limit=limit,
            skip=offset,
            order_by="invoice_date",
            order_desc=True,
        )

    def get_overdue_invoices(
        self, as_of_date: Optional[datetime] = None
    ) -> List[Invoice]:
        """Get all overdue invoices"""
        if not as_of_date:
            as_of_date = datetime.utcnow()

        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.due_date < as_of_date,
                    self.model.status.in_([InvoiceStatus.PENDING, InvoiceStatus.SENT]),
                    self.model.balance_due > 0,
                )
            )
            .all()
        )

    def get_invoices_by_status(
        self, status: InvoiceStatus, limit: int = 100, offset: int = 0
    ) -> List[Invoice]:
        """Get invoices by status"""
        return self.get_all(
            filters={"status": status},
            limit=limit,
            skip=offset,
            order_by="invoice_date",
            order_desc=True,
        )

    def get_invoices_by_date_range(
        self, start_date: date, end_date: date, limit: int = 100, offset: int = 0
    ) -> List[Invoice]:
        """Get invoices within date range"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.invoice_date >= start_date,
                    self.model.invoice_date <= end_date,
                )
            )
            .order_by(desc(self.model.invoice_date))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def search_invoices(self, search_params: Dict[str, Any]) -> List[Invoice]:
        """Advanced invoice search"""
        query = self.db.query(self.model)

        if search_params.get("customer_id"):
            query = query.filter(self.model.customer_id == search_params["customer_id"])

        if search_params.get("status"):
            query = query.filter(self.model.status == search_params["status"])

        if search_params.get("invoice_number"):
            query = query.filter(
                self.model.invoice_number.ilike(f"%{search_params['invoice_number']}%")
            )

        if search_params.get("date_from"):
            query = query.filter(self.model.invoice_date >= search_params["date_from"])

        if search_params.get("date_to"):
            query = query.filter(self.model.invoice_date <= search_params["date_to"])

        if search_params.get("due_date_from"):
            query = query.filter(self.model.due_date >= search_params["due_date_from"])

        if search_params.get("due_date_to"):
            query = query.filter(self.model.due_date <= search_params["due_date_to"])

        if search_params.get("amount_min"):
            query = query.filter(self.model.total_amount >= search_params["amount_min"])

        if search_params.get("amount_max"):
            query = query.filter(self.model.total_amount <= search_params["amount_max"])

        if search_params.get("overdue_only"):
            query = query.filter(
                and_(
                    self.model.due_date < datetime.utcnow(),
                    self.model.status.in_([InvoiceStatus.PENDING, InvoiceStatus.SENT]),
                )
            )

        if search_params.get("unpaid_only"):
            query = query.filter(self.model.balance_due > 0)

        return query.order_by(desc(self.model.invoice_date)).all()

    def get_billing_statistics(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get billing statistics"""
        query = self.db.query(self.model)

        if start_date:
            query = query.filter(self.model.invoice_date >= start_date)
        if end_date:
            query = query.filter(self.model.invoice_date <= end_date)

        # Basic counts and sums
        total_invoices = query.count()
        total_amount = query.with_entities(
            func.sum(self.model.total_amount)
        ).scalar() or Decimal("0")
        paid_amount = query.with_entities(
            func.sum(self.model.paid_amount)
        ).scalar() or Decimal("0")
        outstanding_amount = query.with_entities(
            func.sum(self.model.balance_due)
        ).scalar() or Decimal("0")

        # Status counts
        status_counts = {}
        for status in InvoiceStatus:
            count = query.filter(self.model.status == status).count()
            status_counts[f"{status.value}_invoices"] = count

        # Overdue amount
        overdue_amount = self.db.query(self.model).filter(
            and_(
                self.model.due_date < datetime.utcnow(),
                self.model.status.in_([InvoiceStatus.PENDING, InvoiceStatus.SENT]),
                self.model.balance_due > 0,
            )
        ).with_entities(func.sum(self.model.balance_due)).scalar() or Decimal("0")

        return {
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "outstanding_amount": outstanding_amount,
            "overdue_amount": overdue_amount,
            **status_counts,
        }


class InvoiceItemRepository(BaseRepository[InvoiceItem]):
    """Repository for invoice item management"""

    def __init__(self, db: Session):
        super().__init__(InvoiceItem, db)

    def get_invoice_items(self, invoice_id: int) -> List[InvoiceItem]:
        """Get all items for an invoice"""
        return self.get_all(filters={"invoice_id": invoice_id})

    def calculate_invoice_totals(self, invoice_id: int) -> Dict[str, Decimal]:
        """Calculate totals for an invoice"""
        items = self.get_invoice_items(invoice_id)

        subtotal = sum(item.line_total for item in items)
        tax_amount = sum(item.tax_amount for item in items)
        discount_amount = sum(item.discount_amount for item in items)
        total_amount = subtotal + tax_amount - discount_amount

        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
        }


class PaymentRepository(BaseRepository[Payment]):
    """Repository for payment management"""

    def __init__(self, db: Session):
        super().__init__(Payment, db)

    def get_by_payment_number(self, payment_number: str) -> Optional[Payment]:
        """Get payment by payment number"""
        return (
            self.db.query(self.model)
            .filter(self.model.payment_number == payment_number)
            .first()
        )

    def get_invoice_payments(self, invoice_id: int) -> List[Payment]:
        """Get all payments for an invoice"""
        return self.get_all(
            filters={"invoice_id": invoice_id}, order_by="payment_date", order_desc=True
        )

    def get_customer_payments(
        self, customer_id: int, limit: int = 100, offset: int = 0
    ) -> List[Payment]:
        """Get payments for a specific customer"""
        return self.get_all(
            filters={"customer_id": customer_id},
            limit=limit,
            skip=offset,
            order_by="payment_date",
            order_desc=True,
        )

    def get_payments_by_method(
        self, payment_method: str, limit: int = 100, offset: int = 0
    ) -> List[Payment]:
        """Get payments by payment method"""
        return self.get_all(
            filters={"payment_method": payment_method},
            limit=limit,
            skip=offset,
            order_by="payment_date",
            order_desc=True,
        )

    def search_payments(self, search_params: Dict[str, Any]) -> List[Payment]:
        """Advanced payment search"""
        query = self.db.query(self.model)

        if search_params.get("customer_id"):
            query = query.filter(self.model.customer_id == search_params["customer_id"])

        if search_params.get("invoice_id"):
            query = query.filter(self.model.invoice_id == search_params["invoice_id"])

        if search_params.get("status"):
            query = query.filter(self.model.status == search_params["status"])

        if search_params.get("payment_method"):
            query = query.filter(
                self.model.payment_method == search_params["payment_method"]
            )

        if search_params.get("payment_number"):
            query = query.filter(
                self.model.payment_number.ilike(f"%{search_params['payment_number']}%")
            )

        if search_params.get("date_from"):
            query = query.filter(self.model.payment_date >= search_params["date_from"])

        if search_params.get("date_to"):
            query = query.filter(self.model.payment_date <= search_params["date_to"])

        if search_params.get("amount_min"):
            query = query.filter(self.model.amount >= search_params["amount_min"])

        if search_params.get("amount_max"):
            query = query.filter(self.model.amount <= search_params["amount_max"])

        return query.order_by(desc(self.model.payment_date)).all()


class PaymentRefundRepository(BaseRepository[PaymentRefund]):
    """Repository for payment refund management"""

    def __init__(self, db: Session):
        super().__init__(PaymentRefund, db)

    def get_by_refund_number(self, refund_number: str) -> Optional[PaymentRefund]:
        """Get refund by refund number"""
        return (
            self.db.query(self.model)
            .filter(self.model.refund_number == refund_number)
            .first()
        )

    def get_payment_refunds(self, payment_id: int) -> List[PaymentRefund]:
        """Get all refunds for a payment"""
        return self.get_all(
            filters={"payment_id": payment_id}, order_by=[desc(self.model.refund_date)]
        )


class CreditNoteRepository(BaseRepository[CreditNote]):
    """Repository for credit note management"""

    def __init__(self, db: Session):
        super().__init__(CreditNote, db)

    def get_by_credit_note_number(
        self, credit_note_number: str
    ) -> Optional[CreditNote]:
        """Get credit note by number"""
        return (
            self.db.query(self.model)
            .filter(self.model.credit_note_number == credit_note_number)
            .first()
        )

    def get_invoice_credit_notes(self, invoice_id: int) -> List[CreditNote]:
        """Get all credit notes for an invoice"""
        return self.get_all(
            filters={"invoice_id": invoice_id}, order_by="credit_date", order_desc=True
        )

    def get_customer_credit_notes(
        self, customer_id: int, limit: int = 100, offset: int = 0
    ) -> List[CreditNote]:
        """Get credit notes for a specific customer"""
        return self.get_all(
            filters={"customer_id": customer_id},
            limit=limit,
            skip=offset,
            order_by="credit_date",
            order_desc=True,
        )

    def search_credit_notes(self, search_params: Dict[str, Any]) -> List[CreditNote]:
        """Advanced credit note search"""
        query = self.db.query(self.model)

        if search_params.get("customer_id"):
            query = query.filter(self.model.customer_id == search_params["customer_id"])

        if search_params.get("invoice_id"):
            query = query.filter(self.model.invoice_id == search_params["invoice_id"])

        if search_params.get("reason"):
            query = query.filter(self.model.reason == search_params["reason"])

        if search_params.get("status"):
            query = query.filter(self.model.status == search_params["status"])

        if search_params.get("date_from"):
            query = query.filter(self.model.credit_date >= search_params["date_from"])

        if search_params.get("date_to"):
            query = query.filter(self.model.credit_date <= search_params["date_to"])

        if search_params.get("amount_min"):
            query = query.filter(self.model.amount >= search_params["amount_min"])

        if search_params.get("amount_max"):
            query = query.filter(self.model.amount <= search_params["amount_max"])

        return query.order_by(desc(self.model.credit_date)).all()


class BillingCycleRepository(BaseRepository[BillingCycle]):
    """Repository for billing cycle management"""

    def __init__(self, db: Session):
        super().__init__(BillingCycle, db)

    def get_active_cycles(self) -> List[BillingCycle]:
        """Get all active billing cycles"""
        return self.get_all(filters={"status": "active"})

    def get_cycles_by_type(self, cycle_type: str) -> List[BillingCycle]:
        """Get billing cycles by type"""
        return self.get_all(
            filters={"cycle_type": cycle_type}, order_by=[desc(self.model.start_date)]
        )

    def get_current_cycle(self, cycle_type: str) -> Optional[BillingCycle]:
        """Get current billing cycle for a type"""
        now = datetime.utcnow()
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.cycle_type == cycle_type,
                    self.model.start_date <= now,
                    self.model.end_date >= now,
                    self.model.status == "active",
                )
            )
            .first()
        )


class AccountingEntryRepository(BaseRepository[AccountingEntry]):
    """Repository for accounting entry management"""

    def __init__(self, db: Session):
        from app.models.billing import AccountingEntry

        super().__init__(AccountingEntry, db)

    def get_by_entry_number(self, entry_number: str) -> Optional[AccountingEntry]:
        """Get accounting entry by entry number"""
        return (
            self.db.query(self.model)
            .filter(self.model.entry_number == entry_number)
            .first()
        )

    def get_entries_by_account(
        self, account_code: str, limit: int = 100, offset: int = 0
    ) -> List[AccountingEntry]:
        """Get entries for a specific account"""
        return self.get_all(
            filters={"account_code": account_code},
            limit=limit,
            skip=offset,
            order_by="entry_date",
            order_desc=True,
        )

    def get_entries_by_date_range(
        self, start_date: date, end_date: date, account_code: Optional[str] = None
    ) -> List[AccountingEntry]:
        """Get accounting entries within date range"""
        from sqlalchemy import and_, desc

        query = self.db.query(self.model).filter(
            and_(self.model.entry_date >= start_date, self.model.entry_date <= end_date)
        )

        if account_code:
            query = query.filter(self.model.account_code == account_code)

        return query.order_by(desc(self.model.entry_date)).all()

    def get_trial_balance(
        self, as_of_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get trial balance as of a specific date"""
        from sqlalchemy import func

        query = self.db.query(
            self.model.account_code,
            self.model.account_name,
            func.sum(self.model.debit_amount).label("total_debits"),
            func.sum(self.model.credit_amount).label("total_credits"),
        )

        if as_of_date:
            query = query.filter(self.model.entry_date <= as_of_date)

        return (
            query.group_by(self.model.account_code, self.model.account_name)
            .order_by(self.model.account_code)
            .all()
        )


class TaxRateRepository(BaseRepository[TaxRate]):
    """Repository for tax rate management"""

    def __init__(self, db: Session):
        super().__init__(TaxRate, db)

    def get_active_rates(self) -> List[TaxRate]:
        """Get all active tax rates"""
        return self.get_all(filters={"is_active": True})


#     def get_default_rate(self) -> Optional[TaxRate]:
#         """Get default tax rate"""
#         return self.db.query(self.model).filter(
#             and_(
#                 self.model.is_active == True,
#                 self.model.is_default == True
#             )
#         ).first()
#
#     def get_rate_by_location(
#         self,
#         country: Optional[str] = None,
#         state_province: Optional[str] = None,
#         city: Optional[str] = None,
#         postal_code: Optional[str] = None
#     ) -> Optional[TaxRate]:
#         """Get tax rate by geographic location"""
#         query = self.db.query(self.model).filter(self.model.is_active == True)
#
#         # Most specific match first
#         if postal_code:
#             query = query.filter(self.model.postal_code == postal_code)
#         elif city:
#             query = query.filter(self.model.city == city)
#         elif state_province:
#             query = query.filter(self.model.state_province == state_province)
#         elif country:
#             query = query.filter(self.model.country == country)
#
#         return query.first()

#     def get_effective_rates(self, as_of_date: Optional[datetime] = None) -> List[TaxRate]:
#         """Get tax rates effective as of a specific date"""
#         if not as_of_date:
#             as_of_date = datetime.utcnow()
#
#         return self.db.query(self.model).filter(
#             and_(
#                 self.model.is_active == True,
#                 self.model.effective_date <= as_of_date,
#                 or_(
#                     self.model.expiry_date.is_(None),
#                     self.model.expiry_date > as_of_date
#                 )
#             )
#         ).all()


class BillingManagementRepository:
    """Unified repository for billing management operations"""

    def __init__(self, db: Session):
        self.db = db
        self.invoice_repo = InvoiceRepository(db)
        self.invoice_item_repo = InvoiceItemRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.payment_refund_repo = PaymentRefundRepository(db)
        self.credit_note_repo = CreditNoteRepository(db)
        self.billing_cycle_repo = BillingCycleRepository(db)
        # AccountingEntry and TaxRate repositories are now available
        # self.accounting_entry_repo = AccountingEntryRepository(db)
        # self.tax_rate_repo = TaxRateRepository(db)

    def get_customer_billing_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive billing summary for a customer"""
        # Get customer invoices
        invoices = self.invoice_repo.get_customer_invoices(customer_id)
        payments = self.payment_repo.get_customer_payments(customer_id)
        credit_notes = self.credit_note_repo.get_customer_credit_notes(customer_id)

        # Calculate totals
        total_invoices = len(invoices)
        total_amount = sum(inv.total_amount for inv in invoices)
        paid_amount = sum(inv.paid_amount for inv in invoices)
        outstanding_amount = sum(inv.balance_due for inv in invoices)
        overdue_amount = sum(inv.balance_due for inv in invoices if inv.is_overdue)

        # Get last dates
        last_invoice_date = invoices[0].invoice_date if invoices else None
        last_payment_date = payments[0].payment_date if payments else None

        return {
            "customer_id": customer_id,
            "total_invoices": total_invoices,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "outstanding_amount": outstanding_amount,
            "overdue_amount": overdue_amount,
            "last_invoice_date": last_invoice_date,
            "last_payment_date": last_payment_date,
            "total_payments": len(payments),
            "total_credit_notes": len(credit_notes),
        }
