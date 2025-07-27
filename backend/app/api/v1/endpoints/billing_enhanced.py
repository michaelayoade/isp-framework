"""
Billing API Endpoints

Comprehensive REST API endpoints for the modular billing system with advanced ISP features:
- Billing account management
- Real-time balance operations
- Invoice generation and management
- Payment processing
- Credit note handling
- Payment plan management
- Dunning management
- Billing reports and analytics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_admin
from app.models import Administrator
from app.models.billing import (
    BillingType, AccountStatus, TransactionType, InvoiceStatus,
    PaymentStatus, PaymentMethodType
)
from app.services.billing_service import (
    get_billing_account_service, get_invoice_service,
    get_payment_service, get_billing_report_service,
    BillingAccountService, InvoiceService, PaymentService, BillingReportService
)
from app.schemas.billing_enhanced import (
    BillingAccountCreate, BillingAccountResponse, BillingAccountUpdate,
    BalanceUpdateRequest, BalanceResponse, TransactionResponse,
    InvoiceCreate, InvoiceResponse, InvoiceUpdate, InvoiceItemCreate,
    PaymentCreate, PaymentResponse, PaymentMethodCreate, PaymentMethodResponse,
    CreditNoteCreate, CreditNoteResponse, PaymentPlanCreate, PaymentPlanResponse,
    BillingReportResponse, AccountSummaryResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Billing Account Management Endpoints
@router.post("/accounts", response_model=BillingAccountResponse)
async def create_billing_account(
    account_data: BillingAccountCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    billing_service: BillingAccountService = Depends(get_billing_account_service)
):
    """Create a new billing account for a customer"""
    try:
        account = billing_service.create_billing_account(
            customer_id=account_data.customer_id,
            billing_type=account_data.billing_type,
            account_data=account_data.dict(exclude={'customer_id', 'billing_type'})
        )
        return BillingAccountResponse.from_orm(account)
    except Exception as e:
        logger.error(f"Error creating billing account: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}", response_model=BillingAccountResponse)
async def get_billing_account(
    account_id: int = Path(..., description="Billing account ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    billing_service: BillingAccountService = Depends(get_billing_account_service)
):
    """Get billing account details"""
    try:
        account = billing_service._get_account(account_id)
        return BillingAccountResponse.from_orm(account)
    except Exception as e:
        logger.error(f"Error retrieving billing account: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/accounts/{account_id}/balance", response_model=BalanceResponse)
async def get_account_balance(
    account_id: int = Path(..., description="Billing account ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    billing_service: BillingAccountService = Depends(get_billing_account_service)
):
    """Get current account balance information"""
    try:
        balance_info = billing_service.get_account_balance(account_id)
        return BalanceResponse(**balance_info)
    except Exception as e:
        logger.error(f"Error retrieving account balance: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/accounts/{account_id}/balance", response_model=TransactionResponse)
async def update_account_balance(
    account_id: int = Path(..., description="Billing account ID"),
    balance_update: BalanceUpdateRequest = ...,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    billing_service: BillingAccountService = Depends(get_billing_account_service)
):
    """Update account balance with transaction logging"""
    try:
        transaction = billing_service.update_balance(
            account_id=account_id,
            amount=balance_update.amount,
            transaction_type=balance_update.transaction_type,
            description=balance_update.description,
            reference_id=balance_update.reference_id
        )
        return TransactionResponse.from_orm(transaction)
    except Exception as e:
        logger.error(f"Error updating account balance: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Invoice Management Endpoints
@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Create a new invoice with items"""
    try:
        invoice = invoice_service.create_invoice(
            billing_account_id=invoice_data.billing_account_id,
            invoice_data=invoice_data.dict(exclude={'billing_account_id', 'invoice_items'}),
            invoice_items=[item.dict() for item in invoice_data.invoice_items]
        )
        return InvoiceResponse.from_orm(invoice)
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Get invoice details with items"""
    try:
        invoice = invoice_service._get_invoice(invoice_id)
        return InvoiceResponse.from_orm(invoice)
    except Exception as e:
        logger.error(f"Error retrieving invoice: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/invoices/{invoice_id}/finalize", response_model=InvoiceResponse)
async def finalize_invoice(
    invoice_id: int = Path(..., description="Invoice ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Finalize invoice and make it ready for payment"""
    try:
        invoice = invoice_service.finalize_invoice(invoice_id)
        return InvoiceResponse.from_orm(invoice)
    except Exception as e:
        logger.error(f"Error finalizing invoice: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/invoices", response_model=List[InvoiceResponse])
async def get_account_invoices(
    account_id: int = Path(..., description="Billing account ID"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by invoice status"),
    limit: int = Query(50, description="Number of invoices to return"),
    offset: int = Query(0, description="Number of invoices to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get invoices for a billing account"""
    try:
        from app.repositories.billing_repository import get_invoice_repository
        invoice_repo = get_invoice_repository(db)
        
        if status:
            invoices = invoice_repo.get_by_status(status, account_id)
        else:
            invoices = invoice_repo.get_by_account_id(account_id, limit, offset)
        
        return [InvoiceResponse.from_orm(invoice) for invoice in invoices]
    except Exception as e:
        logger.error(f"Error retrieving account invoices: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Payment Management Endpoints
@router.post("/payments", response_model=PaymentResponse)
async def process_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Process a payment for a billing account"""
    try:
        payment = payment_service.process_payment(
            billing_account_id=payment_data.billing_account_id,
            amount=payment_data.amount,
            payment_method_id=payment_data.payment_method_id,
            invoice_id=payment_data.invoice_id,
            payment_data=payment_data.dict(exclude={
                'billing_account_id', 'amount', 'payment_method_id', 'invoice_id'
            })
        )
        return PaymentResponse.from_orm(payment)
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int = Path(..., description="Payment ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get payment details"""
    try:
        from app.repositories.billing_repository import get_payment_repository
        payment_repo = get_payment_repository(db)
        payment = payment_repo.get(payment_id)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return PaymentResponse.from_orm(payment)
    except Exception as e:
        logger.error(f"Error retrieving payment: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/accounts/{account_id}/payments", response_model=List[PaymentResponse])
async def get_account_payments(
    account_id: int = Path(..., description="Billing account ID"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    limit: int = Query(50, description="Number of payments to return"),
    offset: int = Query(0, description="Number of payments to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get payments for a billing account"""
    try:
        from app.repositories.billing_repository import get_payment_repository
        payment_repo = get_payment_repository(db)
        
        if status:
            payments = payment_repo.get_by_status(status, account_id)
        else:
            payments = payment_repo.get_by_account_id(account_id, limit, offset)
        
        return [PaymentResponse.from_orm(payment) for payment in payments]
    except Exception as e:
        logger.error(f"Error retrieving account payments: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Payment Method Management Endpoints
@router.post("/payment-methods", response_model=PaymentMethodResponse)
async def create_payment_method(
    payment_method_data: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Create a new payment method for a billing account"""
    try:
        payment_method = payment_service.create_payment_method(
            billing_account_id=payment_method_data.billing_account_id,
            method_type=payment_method_data.method_type,
            method_data=payment_method_data.dict(exclude={'billing_account_id', 'method_type'})
        )
        return PaymentMethodResponse.from_orm(payment_method)
    except Exception as e:
        logger.error(f"Error creating payment method: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/payment-methods", response_model=List[PaymentMethodResponse])
async def get_account_payment_methods(
    account_id: int = Path(..., description="Billing account ID"),
    active_only: bool = Query(True, description="Return only active payment methods"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get payment methods for a billing account"""
    try:
        from app.repositories.billing_repository import get_payment_method_repository
        payment_method_repo = get_payment_method_repository(db)
        
        if active_only:
            payment_methods = payment_method_repo.get_active_methods(account_id)
        else:
            payment_methods = payment_method_repo.get_by_account_id(account_id)
        
        return [PaymentMethodResponse.from_orm(method) for method in payment_methods]
    except Exception as e:
        logger.error(f"Error retrieving payment methods: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Credit Note Management Endpoints
@router.post("/credit-notes", response_model=CreditNoteResponse)
async def create_credit_note(
    credit_note_data: CreditNoteCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new credit note"""
    try:
        from app.models.billing import CreditNote
        
        # Generate credit note number
        credit_number = f"CN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        credit_note = CreditNote(
            credit_number=credit_number,
            **credit_note_data.dict()
        )
        
        db.add(credit_note)
        db.commit()
        db.refresh(credit_note)
        
        return CreditNoteResponse.from_orm(credit_note)
    except Exception as e:
        logger.error(f"Error creating credit note: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/credit-notes", response_model=List[CreditNoteResponse])
async def get_account_credit_notes(
    account_id: int = Path(..., description="Billing account ID"),
    limit: int = Query(50, description="Number of credit notes to return"),
    offset: int = Query(0, description="Number of credit notes to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get credit notes for a billing account"""
    try:
        from app.repositories.billing_repository import get_credit_note_repository
        credit_note_repo = get_credit_note_repository(db)
        credit_notes = credit_note_repo.get_by_account_id(account_id, limit, offset)
        
        return [CreditNoteResponse.from_orm(note) for note in credit_notes]
    except Exception as e:
        logger.error(f"Error retrieving credit notes: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Payment Plan Management Endpoints
@router.post("/payment-plans", response_model=PaymentPlanResponse)
async def create_payment_plan(
    payment_plan_data: PaymentPlanCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new payment plan"""
    try:
        from app.models.billing import PaymentPlan
        
        payment_plan = PaymentPlan(**payment_plan_data.dict())
        db.add(payment_plan)
        db.commit()
        db.refresh(payment_plan)
        
        return PaymentPlanResponse.from_orm(payment_plan)
    except Exception as e:
        logger.error(f"Error creating payment plan: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/accounts/{account_id}/payment-plans", response_model=List[PaymentPlanResponse])
async def get_account_payment_plans(
    account_id: int = Path(..., description="Billing account ID"),
    active_only: bool = Query(True, description="Return only active payment plans"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get payment plans for a billing account"""
    try:
        from app.repositories.billing_repository import get_payment_plan_repository
        payment_plan_repo = get_payment_plan_repository(db)
        
        if active_only:
            payment_plans = payment_plan_repo.get_active_plans(account_id)
        else:
            payment_plans = payment_plan_repo.get_by_account_id(account_id)
        
        return [PaymentPlanResponse.from_orm(plan) for plan in payment_plans]
    except Exception as e:
        logger.error(f"Error retrieving payment plans: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Billing Reports and Analytics Endpoints
@router.get("/accounts/{account_id}/summary", response_model=AccountSummaryResponse)
async def get_account_summary(
    account_id: int = Path(..., description="Billing account ID"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin),
    report_service: BillingReportService = Depends(get_billing_report_service)
):
    """Get comprehensive account summary with analytics"""
    try:
        summary = report_service.get_account_summary(account_id)
        return AccountSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error generating account summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/billing-overview", response_model=BillingReportResponse)
async def get_billing_overview(
    start_date: Optional[datetime] = Query(None, description="Start date for report"),
    end_date: Optional[datetime] = Query(None, description="End date for report"),
    billing_type: Optional[BillingType] = Query(None, description="Filter by billing type"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get billing system overview report"""
    try:
        from app.repositories.billing_repository import (
            get_billing_account_repository, get_invoice_repository, get_payment_repository
        )
        
        account_repo = get_billing_account_repository(db)
        invoice_repo = get_invoice_repository(db)
        payment_repo = get_payment_repository(db)
        
        # Get basic statistics
        total_accounts = len(account_repo.get_all())
        active_accounts = len(account_repo.get_accounts_by_status(AccountStatus.ACTIVE))
        
        # Get invoice statistics
        pending_invoices = len(invoice_repo.get_by_status(InvoiceStatus.PENDING))
        overdue_invoices = len(invoice_repo.get_overdue_invoices())
        
        # Get payment statistics
        completed_payments = len(payment_repo.get_by_status(PaymentStatus.COMPLETED))
        failed_payments = len(payment_repo.get_by_status(PaymentStatus.FAILED))
        
        report_data = {
            "report_date": datetime.now(timezone.utc),
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "pending_invoices": pending_invoices,
            "overdue_invoices": overdue_invoices,
            "completed_payments": completed_payments,
            "failed_payments": failed_payments,
            "billing_type_filter": billing_type,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
        return BillingReportResponse(**report_data)
    except Exception as e:
        logger.error(f"Error generating billing overview: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Transaction History Endpoints
@router.get("/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: int = Path(..., description="Billing account ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    start_date: Optional[datetime] = Query(None, description="Start date for transactions"),
    end_date: Optional[datetime] = Query(None, description="End date for transactions"),
    limit: int = Query(100, description="Number of transactions to return"),
    offset: int = Query(0, description="Number of transactions to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get transaction history for a billing account"""
    try:
        from app.repositories.billing_repository import get_billing_transaction_repository
        transaction_repo = get_billing_transaction_repository(db)
        
        if start_date and end_date:
            transactions = transaction_repo.get_transactions_by_date_range(
                account_id, start_date, end_date
            )
        elif transaction_type:
            transactions = transaction_repo.get_by_transaction_type(account_id, transaction_type)
        else:
            transactions = transaction_repo.get_by_account_id(account_id, limit, offset)
        
        return [TransactionResponse.from_orm(transaction) for transaction in transactions]
    except Exception as e:
        logger.error(f"Error retrieving account transactions: {e}")
        raise HTTPException(status_code=400, detail=str(e))
