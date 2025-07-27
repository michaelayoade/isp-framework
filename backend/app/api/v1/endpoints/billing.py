"""
Billing System API Endpoints

Complete FastAPI endpoints for billing module including invoices, payments,
credit notes, and accounting for ISP Framework.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ....core.database import get_db
from ..dependencies import get_current_admin
from ....models.auth import Administrator
from ....services.billing import (
    InvoiceService, PaymentService, CreditNoteService, BillingManagementService
)
from ....schemas.billing import (
    # Invoice schemas
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceSearch,
    InvoiceItemCreate, InvoiceItemUpdate, InvoiceItemResponse,
    
    # Payment schemas
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentSearch,
    PaymentRefundCreate, PaymentRefundUpdate, PaymentRefundResponse,
    
    # Credit note schemas
    CreditNoteCreate, CreditNoteUpdate, CreditNoteResponse, CreditNoteSearch,
    
    # Summary schemas
    BillingOverview, CustomerBillingSummary
)

router = APIRouter()


# Invoice Management Endpoints
@router.post("/invoices/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new invoice"""
    try:
        invoice_service = InvoiceService(db)
        invoice = invoice_service.create_invoice(invoice_data)
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create invoice")


@router.get("/invoices/", response_model=List[InvoiceResponse])
async def search_invoices(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    status: Optional[str] = Query(None, description="Filter by invoice status"),
    invoice_number: Optional[str] = Query(None, description="Filter by invoice number"),
    date_from: Optional[date] = Query(None, description="Filter by invoice date from"),
    date_to: Optional[date] = Query(None, description="Filter by invoice date to"),
    overdue_only: bool = Query(False, description="Show only overdue invoices"),
    unpaid_only: bool = Query(False, description="Show only unpaid invoices"),
    limit: int = Query(100, ge=1, le=1000, description="Number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Search invoices with filters"""
    try:
        invoice_service = InvoiceService(db)
        
        # Build search parameters
        search_params = InvoiceSearch(
            customer_id=customer_id,
            status=status,
            invoice_number=invoice_number,
            date_from=date_from,
            date_to=date_to,
            overdue_only=overdue_only,
            unpaid_only=unpaid_only
        )
        
        invoices = invoice_service.search_invoices(search_params)
        
        # Apply pagination
        return invoices[offset:offset + limit]
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search invoices")


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get invoice by ID"""
    try:
        invoice_service = InvoiceService(db)
        invoice = invoice_service.invoice_repo.get(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        return invoice
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get invoice")


@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Update an existing invoice"""
    try:
        invoice_service = InvoiceService(db)
        invoice = invoice_service.update_invoice(invoice_id, invoice_data)
        
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update invoice")


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Send an invoice to customer"""
    try:
        invoice_service = InvoiceService(db)
        invoice = invoice_service.send_invoice(invoice_id)
        
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send invoice")


@router.post("/invoices/{invoice_id}/cancel", response_model=InvoiceResponse)
async def cancel_invoice(
    invoice_id: int,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Cancel an invoice"""
    try:
        invoice_service = InvoiceService(db)
        invoice = invoice_service.cancel_invoice(invoice_id, reason)
        
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        return invoice
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel invoice")


@router.post("/invoices/{invoice_id}/items", response_model=InvoiceItemResponse, status_code=status.HTTP_201_CREATED)
async def add_invoice_item(
    invoice_id: int,
    item_data: InvoiceItemCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Add an item to an invoice"""
    try:
        invoice_service = InvoiceService(db)
        item = invoice_service.add_invoice_item(invoice_id, item_data)
        
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        return item
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add invoice item")


@router.get("/invoices/overdue", response_model=List[InvoiceResponse])
async def get_overdue_invoices(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get all overdue invoices"""
    try:
        invoice_service = InvoiceService(db)
        invoices = invoice_service.get_overdue_invoices()
        return invoices
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get overdue invoices")


@router.get("/customers/{customer_id}/invoices", response_model=List[InvoiceResponse])
async def get_customer_invoices(
    customer_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get invoices for a specific customer"""
    try:
        invoice_service = InvoiceService(db)
        invoices = invoice_service.get_customer_invoices(customer_id, limit, offset)
        return invoices
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customer invoices")


# Payment Management Endpoints
@router.post("/payments/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new payment"""
    try:
        payment_service = PaymentService(db)
        payment = payment_service.create_payment(payment_data)
        return payment
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create payment")


@router.get("/payments/", response_model=List[PaymentResponse])
async def search_payments(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    invoice_id: Optional[int] = Query(None, description="Filter by invoice ID"),
    status: Optional[str] = Query(None, description="Filter by payment status"),
    payment_method: Optional[str] = Query(None, description="Filter by payment method"),
    payment_number: Optional[str] = Query(None, description="Filter by payment number"),
    date_from: Optional[date] = Query(None, description="Filter by payment date from"),
    date_to: Optional[date] = Query(None, description="Filter by payment date to"),
    limit: int = Query(100, ge=1, le=1000, description="Number of payments to return"),
    offset: int = Query(0, ge=0, description="Number of payments to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Search payments with filters"""
    try:
        payment_service = PaymentService(db)
        
        # Build search parameters
        search_params = PaymentSearch(
            customer_id=customer_id,
            invoice_id=invoice_id,
            status=status,
            payment_method=payment_method,
            payment_number=payment_number,
            date_from=date_from,
            date_to=date_to
        )
        
        payments = payment_service.search_payments(search_params)
        
        # Apply pagination
        return payments[offset:offset + limit]
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search payments")


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get payment by ID"""
    try:
        payment_service = PaymentService(db)
        payment = payment_service.payment_repo.get(payment_id)
        
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get payment")


@router.get("/invoices/{invoice_id}/payments", response_model=List[PaymentResponse])
async def get_invoice_payments(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get all payments for an invoice"""
    try:
        payment_service = PaymentService(db)
        payments = payment_service.payment_repo.get_invoice_payments(invoice_id)
        return payments
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get invoice payments")


@router.get("/customers/{customer_id}/payments", response_model=List[PaymentResponse])
async def get_customer_payments(
    customer_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Number of payments to return"),
    offset: int = Query(0, ge=0, description="Number of payments to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get payments for a specific customer"""
    try:
        payment_service = PaymentService(db)
        payments = payment_service.payment_repo.get_customer_payments(customer_id, limit, offset)
        return payments
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customer payments")


# Credit Note Management Endpoints
@router.post("/credit-notes/", response_model=CreditNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_credit_note(
    credit_note_data: CreditNoteCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create a new credit note"""
    try:
        credit_note_service = CreditNoteService(db)
        credit_note = credit_note_service.create_credit_note(credit_note_data)
        return credit_note
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create credit note")


@router.get("/credit-notes/", response_model=List[CreditNoteResponse])
async def search_credit_notes(
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    invoice_id: Optional[int] = Query(None, description="Filter by invoice ID"),
    reason: Optional[str] = Query(None, description="Filter by credit note reason"),
    status: Optional[str] = Query(None, description="Filter by credit note status"),
    date_from: Optional[date] = Query(None, description="Filter by credit date from"),
    date_to: Optional[date] = Query(None, description="Filter by credit date to"),
    limit: int = Query(100, ge=1, le=1000, description="Number of credit notes to return"),
    offset: int = Query(0, ge=0, description="Number of credit notes to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Search credit notes with filters"""
    try:
        credit_note_service = CreditNoteService(db)
        
        # Build search parameters
        search_params = CreditNoteSearch(
            customer_id=customer_id,
            invoice_id=invoice_id,
            reason=reason,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        
        credit_notes = credit_note_service.search_credit_notes(search_params)
        
        # Apply pagination
        return credit_notes[offset:offset + limit]
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search credit notes")


@router.get("/credit-notes/{credit_note_id}", response_model=CreditNoteResponse)
async def get_credit_note(
    credit_note_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get credit note by ID"""
    try:
        credit_note_service = CreditNoteService(db)
        credit_note = credit_note_service.credit_note_repo.get(credit_note_id)
        
        if not credit_note:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit note not found")
        
        return credit_note
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get credit note")


@router.get("/invoices/{invoice_id}/credit-notes", response_model=List[CreditNoteResponse])
async def get_invoice_credit_notes(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get all credit notes for an invoice"""
    try:
        credit_note_service = CreditNoteService(db)
        credit_notes = credit_note_service.credit_note_repo.get_invoice_credit_notes(invoice_id)
        return credit_notes
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get invoice credit notes")


@router.get("/customers/{customer_id}/credit-notes", response_model=List[CreditNoteResponse])
async def get_customer_credit_notes(
    customer_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Number of credit notes to return"),
    offset: int = Query(0, ge=0, description="Number of credit notes to skip"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get credit notes for a specific customer"""
    try:
        credit_note_service = CreditNoteService(db)
        credit_notes = credit_note_service.credit_note_repo.get_customer_credit_notes(customer_id, limit, offset)
        return credit_notes
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customer credit notes")


# Billing Overview and Statistics Endpoints
@router.get("/overview", response_model=BillingOverview)
async def get_billing_overview(
    start_date: Optional[date] = Query(None, description="Start date for statistics"),
    end_date: Optional[date] = Query(None, description="End date for statistics"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive billing overview and statistics"""
    try:
        billing_service = BillingManagementService(db)
        overview = billing_service.get_billing_overview(start_date, end_date)
        return overview
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get billing overview")


@router.get("/customers/{customer_id}/billing-summary", response_model=CustomerBillingSummary)
async def get_customer_billing_summary(
    customer_id: int,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get comprehensive billing summary for a customer"""
    try:
        billing_service = BillingManagementService(db)
        summary = billing_service.get_customer_billing_summary(customer_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get customer billing summary")


@router.get("/statistics", response_model=dict)
async def get_billing_statistics(
    start_date: Optional[date] = Query(None, description="Start date for statistics"),
    end_date: Optional[date] = Query(None, description="End date for statistics"),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Get detailed billing statistics"""
    try:
        invoice_service = InvoiceService(db)
        statistics = invoice_service.get_billing_statistics(start_date, end_date)
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get billing statistics")
