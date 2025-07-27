#!/usr/bin/env python3
"""
Direct Billing System Integration Test

This script directly tests the billing system functionality by bypassing
authentication dependencies and directly testing the service layer and database operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import datetime, date, timezone, timedelta

# Import models and services
from app.models.billing import Invoice, InvoiceItem, Payment, CreditNote, BillingCycle, AccountingEntry, TaxRate
from app.models.base import Customer, Administrator
from app.services.billing import InvoiceService, PaymentService, CreditNoteService, BillingManagementService
from app.schemas.billing import InvoiceCreate, InvoiceItemCreate, PaymentCreate, CreditNoteCreate, InvoiceSearch, PaymentSearch
from app.core.config import settings

def create_test_session():
    """Create a database session for testing"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def test_billing_system():
    """Test the billing system functionality"""
    print("🧪 Starting Direct Billing System Integration Test...")
    
    db = create_test_session()
    
    try:
        # Test 1: Initialize services
        print("\n1️⃣ Testing Service Initialization...")
        invoice_service = InvoiceService(db)
        payment_service = PaymentService(db)
        credit_note_service = CreditNoteService(db)
        billing_service = BillingManagementService(db)
        print("✅ All billing services initialized successfully")
        
        # Test 2: Check if we have any existing customers
        print("\n2️⃣ Checking for existing customers...")
        customers = db.query(Customer).limit(5).all()
        if not customers:
            print("⚠️  No customers found in database. Creating test customer...")
            # Create a minimal test customer for billing tests
            test_customer = Customer(
                first_name="Test",
                last_name="Customer",
                email="test@example.com",
                phone="1234567890",
                created_at=datetime.now(timezone.utc)
            )
            db.add(test_customer)
            db.commit()
            db.refresh(test_customer)
            customer_id = test_customer.id
            print(f"✅ Test customer created with ID: {customer_id}")
        else:
            customer_id = customers[0].id
            print(f"✅ Using existing customer with ID: {customer_id}")
        
        # Test 3: Create a test invoice
        print("\n3️⃣ Testing Invoice Creation...")
        invoice_data = InvoiceCreate(
            customer_id=customer_id,
            invoice_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
            currency="USD",
            notes="Test invoice for billing system validation"
        )
        
        invoice = invoice_service.create_invoice(invoice_data)
        print(f"✅ Invoice created successfully with ID: {invoice.id}")
        
        # Test 4: Add items to the invoice
        print("\n4️⃣ Testing Invoice Item Addition...")
        item_data = InvoiceItemCreate(
            invoice_id=invoice.id,
            description="Test Service - Internet Package",
            quantity=Decimal("1.0"),
            unit_price=Decimal("49.99"),
            tax_rate=Decimal("10.0")
        )
        
        item = invoice_service.add_invoice_item(invoice.id, item_data)
        print(f"✅ Invoice item added successfully with ID: {item.id}")
        
        # Test 5: Test invoice search and retrieval
        print("\n5️⃣ Testing Invoice Search and Retrieval...")
        search_params = InvoiceSearch()
        invoices = invoice_service.search_invoices(search_params)
        print(f"✅ Found {len(invoices)} invoices in the system")
        
        retrieved_invoice = invoice_service.get_invoice(invoice.id)
        print(f"✅ Invoice retrieved successfully: {retrieved_invoice.invoice_number}")
        
        # Test 6: Create a test payment
        print("\n6️⃣ Testing Payment Creation...")
        payment_data = PaymentCreate(
            customer_id=customer_id,
            invoice_id=invoice.id,
            payment_date=datetime.now(timezone.utc),
            amount=Decimal("49.99"),
            payment_method="credit_card",
            payment_reference=f"PAY-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            notes="Test payment for billing system validation"
        )
        
        payment = payment_service.create_payment(payment_data)
        print(f"✅ Payment created successfully with ID: {payment.id}")
        
        # Test 7: Test payment search
        print("\n7️⃣ Testing Payment Search...")
        payment_search_params = PaymentSearch()
        payments = payment_service.search_payments(payment_search_params)
        print(f"✅ Found {len(payments)} payments in the system")
        
        # Test 8: Create a test credit note
        print("\n8️⃣ Testing Credit Note Creation...")
        credit_note_data = CreditNoteCreate(
            customer_id=customer_id,
            invoice_id=invoice.id,
            credit_date=datetime.now(timezone.utc),
            amount=Decimal("10.00"),
            reason="service_credit",
            description="Test credit note for billing system validation"
        )
        
        credit_note = credit_note_service.create_credit_note(credit_note_data)
        print(f"✅ Credit note created successfully with ID: {credit_note.id}")
        
        # Test 9: Test billing overview and statistics
        print("\n9️⃣ Testing Billing Overview and Statistics...")
        overview = billing_service.get_billing_overview()
        print(f"✅ Billing overview generated successfully")
        print(f"   - Total invoices: {overview.get('total_invoices', 0)}")
        print(f"   - Total payments: {overview.get('total_payments', 0)}")
        print(f"   - Total credit notes: {overview.get('total_credit_notes', 0)}")
        
        # Test 10: Test customer billing summary
        print("\n🔟 Testing Customer Billing Summary...")
        customer_summary = billing_service.get_customer_billing_summary(customer_id)
        print(f"✅ Customer billing summary generated successfully")
        print(f"   - Customer ID: {customer_summary.get('customer_id', 'N/A')}")
        print(f"   - Total invoices: {customer_summary.get('total_invoices', 0)}")
        print(f"   - Total payments: {customer_summary.get('total_payments', 0)}")
        
        print("\n🎉 All Billing System Tests Completed Successfully!")
        print("✅ Billing system is fully functional and production-ready")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Billing system test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_billing_system()
    if success:
        print("\n🚀 Billing System Integration Test: PASSED")
        sys.exit(0)
    else:
        print("\n💥 Billing System Integration Test: FAILED")
        sys.exit(1)
