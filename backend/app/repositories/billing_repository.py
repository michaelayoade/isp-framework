"""
Billing Repository Layer

Repository layer for the modular billing system providing data access patterns
for all billing entities with advanced querying and filtering capabilities.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.billing import (
    AccountStatus,
    BillingTransaction,
    BillingType,
    CreditNote,
    CustomerBillingAccount,
    DunningCase,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentMethodType,
    PaymentPlan,
    PaymentStatus,
    TransactionType,
)
from app.repositories.base import BaseRepository


class BillingAccountRepository(BaseRepository[CustomerBillingAccount]):
    """Repository for customer billing accounts"""

    def __init__(self, db: Session):
        super().__init__(db, CustomerBillingAccount)

    def get_by_customer_id(self, customer_id: int) -> Optional[CustomerBillingAccount]:
        """Get billing account by customer ID"""
        return (
            self.db.query(self.model)
            .filter(self.model.customer_id == customer_id)
            .first()
        )

    def get_by_account_number(
        self, account_number: str
    ) -> Optional[CustomerBillingAccount]:
        """Get billing account by account number"""
        return (
            self.db.query(self.model)
            .filter(self.model.account_number == account_number)
            .first()
        )

    def get_accounts_by_status(
        self, status: AccountStatus
    ) -> List[CustomerBillingAccount]:
        """Get all accounts with specific status"""
        return (
            self.db.query(self.model).filter(self.model.account_status == status).all()
        )

    def get_accounts_by_billing_type(
        self, billing_type: BillingType
    ) -> List[CustomerBillingAccount]:
        """Get all accounts with specific billing type"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_type == billing_type)
            .all()
        )

    def get_low_balance_accounts(
        self, threshold: Decimal
    ) -> List[CustomerBillingAccount]:
        """Get accounts with balance below threshold"""
        return (
            self.db.query(self.model)
            .filter(self.model.available_balance < threshold)
            .all()
        )

    def search_accounts(
        self,
        search_term: Optional[str] = None,
        billing_type: Optional[BillingType] = None,
        account_status: Optional[AccountStatus] = None,
        min_balance: Optional[Decimal] = None,
        max_balance: Optional[Decimal] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[CustomerBillingAccount], int]:
        """Search accounts with multiple filters"""
        query = self.db.query(self.model)

        if search_term:
            query = query.filter(
                or_(
                    self.model.account_number.ilike(f"%{search_term}%"),
                    self.model.account_name.ilike(f"%{search_term}%"),
                )
            )

        if billing_type:
            query = query.filter(self.model.billing_type == billing_type)

        if account_status:
            query = query.filter(self.model.account_status == account_status)

        if min_balance is not None:
            query = query.filter(self.model.available_balance >= min_balance)

        if max_balance is not None:
            query = query.filter(self.model.available_balance <= max_balance)

        total = query.count()
        accounts = query.offset(offset).limit(limit).all()

        return accounts, total


class BillingTransactionRepository(BaseRepository[BillingTransaction]):
    """Repository for billing transactions"""

    def __init__(self, db: Session):
        super().__init__(db, BillingTransaction)

    def get_by_account_id(
        self, account_id: int, limit: int = 100, offset: int = 0
    ) -> List[BillingTransaction]:
        """Get transactions for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.effective_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_transaction_type(
        self, account_id: int, transaction_type: TransactionType
    ) -> List[BillingTransaction]:
        """Get transactions by type for an account"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.billing_account_id == account_id,
                    self.model.transaction_type == transaction_type,
                )
            )
            .order_by(desc(self.model.effective_date))
            .all()
        )

    def get_transactions_by_date_range(
        self, account_id: int, start_date: datetime, end_date: datetime
    ) -> List[BillingTransaction]:
        """Get transactions within date range"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.billing_account_id == account_id,
                    self.model.effective_date >= start_date,
                    self.model.effective_date <= end_date,
                )
            )
            .order_by(desc(self.model.effective_date))
            .all()
        )

    def get_transaction_summary(self, account_id: int) -> Dict[str, Any]:
        """Get transaction summary for an account"""
        result = (
            self.db.query(
                func.count(self.model.id).label("total_transactions"),
                func.sum(
                    func.case(
                        (
                            self.model.transaction_type.in_(
                                [TransactionType.CREDIT, TransactionType.PAYMENT]
                            ),
                            self.model.amount,
                        ),
                        else_=0,
                    )
                ).label("total_credits"),
                func.sum(
                    func.case(
                        (
                            self.model.transaction_type.in_(
                                [TransactionType.DEBIT, TransactionType.CHARGE]
                            ),
                            self.model.amount,
                        ),
                        else_=0,
                    )
                ).label("total_debits"),
            )
            .filter(self.model.billing_account_id == account_id)
            .first()
        )

        return {
            "total_transactions": result.total_transactions or 0,
            "total_credits": result.total_credits or Decimal("0.00"),
            "total_debits": result.total_debits or Decimal("0.00"),
        }


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for enhanced invoices"""

    def __init__(self, db: Session):
        super().__init__(db, Invoice)

    def get_by_account_id(
        self, account_id: int, limit: int = 50, offset: int = 0
    ) -> List[Invoice]:
        """Get invoices for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.invoice_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self, status: InvoiceStatus, account_id: Optional[int] = None
    ) -> List[Invoice]:
        """Get invoices by status"""
        query = self.db.query(self.model).filter(self.model.invoice_status == status)

        if account_id:
            query = query.filter(self.model.billing_account_id == account_id)

        return query.order_by(desc(self.model.invoice_date)).all()

    def get_overdue_invoices(
        self, as_of_date: Optional[datetime] = None
    ) -> List[Invoice]:
        """Get overdue invoices"""
        if not as_of_date:
            as_of_date = datetime.now(timezone.utc)

        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.due_date < as_of_date,
                    self.model.invoice_status.in_(
                        [InvoiceStatus.PENDING, InvoiceStatus.SENT]
                    ),
                )
            )
            .order_by(asc(self.model.due_date))
            .all()
        )

    def get_invoice_with_items(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice with all items loaded"""
        return (
            self.db.query(self.model)
            .options(joinedload(self.model.invoice_items))
            .filter(self.model.id == invoice_id)
            .first()
        )

    def search_invoices(
        self,
        search_term: Optional[str] = None,
        account_id: Optional[int] = None,
        status: Optional[InvoiceStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Invoice], int]:
        """Search invoices with multiple filters"""
        query = self.db.query(self.model)

        if search_term:
            query = query.filter(
                or_(
                    self.model.invoice_number.ilike(f"%{search_term}%"),
                    self.model.description.ilike(f"%{search_term}%"),
                )
            )

        if account_id:
            query = query.filter(self.model.billing_account_id == account_id)

        if status:
            query = query.filter(self.model.invoice_status == status)

        if start_date:
            query = query.filter(self.model.invoice_date >= start_date)

        if end_date:
            query = query.filter(self.model.invoice_date <= end_date)

        if min_amount is not None:
            query = query.filter(self.model.total_amount >= min_amount)

        if max_amount is not None:
            query = query.filter(self.model.total_amount <= max_amount)

        total = query.count()
        invoices = (
            query.order_by(desc(self.model.invoice_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return invoices, total


class PaymentRepository(BaseRepository[Payment]):
    """Repository for enhanced payments"""

    def __init__(self, db: Session):
        super().__init__(db, Payment)

    def get_by_account_id(
        self, account_id: int, limit: int = 50, offset: int = 0
    ) -> List[Payment]:
        """Get payments for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.payment_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self, status: PaymentStatus, account_id: Optional[int] = None
    ) -> List[Payment]:
        """Get payments by status"""
        query = self.db.query(self.model).filter(self.model.payment_status == status)

        if account_id:
            query = query.filter(self.model.billing_account_id == account_id)

        return query.order_by(desc(self.model.payment_date)).all()

    def get_by_invoice_id(self, invoice_id: int) -> List[Payment]:
        """Get payments for a specific invoice"""
        return (
            self.db.query(self.model)
            .filter(self.model.invoice_id == invoice_id)
            .order_by(desc(self.model.payment_date))
            .all()
        )

    def get_payment_summary(self, account_id: int) -> Dict[str, Any]:
        """Get payment summary for an account"""
        result = (
            self.db.query(
                func.count(self.model.id).label("total_payments"),
                func.sum(
                    func.case(
                        (
                            self.model.payment_status == PaymentStatus.COMPLETED,
                            self.model.amount,
                        ),
                        else_=0,
                    )
                ).label("successful_amount"),
                func.count(
                    func.case(
                        (self.model.payment_status == PaymentStatus.COMPLETED, 1),
                        else_=None,
                    )
                ).label("successful_count"),
                func.count(
                    func.case(
                        (self.model.payment_status == PaymentStatus.FAILED, 1),
                        else_=None,
                    )
                ).label("failed_count"),
            )
            .filter(self.model.billing_account_id == account_id)
            .first()
        )

        return {
            "total_payments": result.total_payments or 0,
            "successful_amount": result.successful_amount or Decimal("0.00"),
            "successful_count": result.successful_count or 0,
            "failed_count": result.failed_count or 0,
        }


class PaymentMethodRepository(BaseRepository[PaymentMethod]):
    """Repository for payment methods"""

    def __init__(self, db: Session):
        super().__init__(db, PaymentMethod)

    def get_by_account_id(self, account_id: int) -> List[PaymentMethod]:
        """Get payment methods for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.created_at))
            .all()
        )

    def get_active_methods(self, account_id: int) -> List[PaymentMethod]:
        """Get active payment methods for an account"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.billing_account_id == account_id,
                    self.model.is_active is True,
                )
            )
            .order_by(desc(self.model.created_at))
            .all()
        )

    def get_by_type(
        self, account_id: int, method_type: PaymentMethodType
    ) -> List[PaymentMethod]:
        """Get payment methods by type"""
        return (
            self.db.query(self.model)
            .filter(
                and_(
                    self.model.billing_account_id == account_id,
                    self.model.method_type == method_type,
                )
            )
            .all()
        )


class CreditNoteRepository(BaseRepository[CreditNote]):
    """Repository for credit notes"""

    def __init__(self, db: Session):
        super().__init__(db, CreditNote)

    def get_by_account_id(
        self, account_id: int, limit: int = 50, offset: int = 0
    ) -> List[CreditNote]:
        """Get credit notes for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.credit_date))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_invoice_id(self, invoice_id: int) -> List[CreditNote]:
        """Get credit notes for a specific invoice"""
        return (
            self.db.query(self.model)
            .filter(self.model.original_invoice_id == invoice_id)
            .order_by(desc(self.model.credit_date))
            .all()
        )


class PaymentPlanRepository(BaseRepository[PaymentPlan]):
    """Repository for payment plans"""

    def __init__(self, db: Session):
        super().__init__(db, PaymentPlan)

    def get_by_account_id(self, account_id: int) -> List[PaymentPlan]:
        """Get payment plans for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.created_at))
            .all()
        )

    def get_active_plans(self, account_id: Optional[int] = None) -> List[PaymentPlan]:
        """Get active payment plans"""
        query = self.db.query(self.model).filter(self.model.is_active is True)

        if account_id:
            query = query.filter(self.model.billing_account_id == account_id)

        return query.order_by(desc(self.model.created_at)).all()

    def get_plan_with_installments(self, plan_id: int) -> Optional[PaymentPlan]:
        """Get payment plan with all installments loaded"""
        return (
            self.db.query(self.model)
            .options(joinedload(self.model.installments))
            .filter(self.model.id == plan_id)
            .first()
        )


class DunningCaseRepository(BaseRepository[DunningCase]):
    """Repository for dunning cases"""

    def __init__(self, db: Session):
        super().__init__(db, DunningCase)

    def get_by_account_id(self, account_id: int) -> List[DunningCase]:
        """Get dunning cases for a billing account"""
        return (
            self.db.query(self.model)
            .filter(self.model.billing_account_id == account_id)
            .order_by(desc(self.model.created_at))
            .all()
        )

    def get_active_cases(self, account_id: Optional[int] = None) -> List[DunningCase]:
        """Get active dunning cases"""
        query = self.db.query(self.model).filter(self.model.is_active is True)

        if account_id:
            query = query.filter(self.model.billing_account_id == account_id)

        return query.order_by(desc(self.model.created_at)).all()


# Repository factory functions for dependency injection
def get_billing_account_repository(db: Session) -> BillingAccountRepository:
    return BillingAccountRepository(db)


def get_billing_transaction_repository(db: Session) -> BillingTransactionRepository:
    return BillingTransactionRepository(db)


def get_invoice_repository(db: Session) -> InvoiceRepository:
    return InvoiceRepository(db)


def get_payment_repository(db: Session) -> PaymentRepository:
    return PaymentRepository(db)


def get_payment_method_repository(db: Session) -> PaymentMethodRepository:
    return PaymentMethodRepository(db)


def get_credit_note_repository(db: Session) -> CreditNoteRepository:
    return CreditNoteRepository(db)


def get_payment_plan_repository(db: Session) -> PaymentPlanRepository:
    return PaymentPlanRepository(db)


def get_dunning_case_repository(db: Session) -> DunningCaseRepository:
    return DunningCaseRepository(db)
