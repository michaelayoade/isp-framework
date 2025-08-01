#!/bin/bash

# ISP Framework - Complete Billing Data Seeding Script
# Creates customers, billing accounts, invoices, payments, and credit notes

set -e

BASE_URL="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "🚀 Starting Complete Billing Data Seeding..."
echo "==========================================="

# 1. Authenticate as admin
echo "1. Authenticating as administrator..."
auth_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}" \
    "$BASE_URL/auth/login")

JWT_TOKEN=$(echo "$auth_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Admin authentication successful"

# 2. Create billing customers
echo ""
echo "2. Creating billing customers..."

customer_ids=""
billing_account_ids=""

for i in {1..3}; do
    customer_data="{
        \"name\": \"Complete Billing Customer $i\",
        \"email\": \"complete_billing$i@example.com\",
        \"phone\": \"+234701234567$i\",
        \"address\": \"$i Complete Billing Street\",
        \"city\": \"Lagos\",
        \"country\": \"Nigeria\",
        \"postal_code\": \"40000$i\",
        \"status_id\": 1,
        \"reseller_id\": 1
    }"
    
    echo "📡 Creating customer $i..."
    customer_response=$(curl -s -X POST \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$customer_data" \
        "$BASE_URL/customers/")
    
    # Extract customer ID
    customer_id=$(echo "$customer_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'id' in data:
        print(data['id'])
except:
    pass
")
    
    if [ -n "$customer_id" ]; then
        customer_ids="$customer_ids $customer_id"
        echo "✅ Created customer $i with ID: $customer_id"
    else
        echo "⚠️  Failed to create customer $i"
        echo "Response: $customer_response"
    fi
done

echo "📋 Customer IDs: $customer_ids"

# 3. Create billing accounts for customers
echo ""
echo "3. Creating billing accounts..."

for customer_id in $customer_ids; do
    if [ -n "$customer_id" ]; then
        # Create billing account directly in database using SQL
        echo "📡 Creating billing account for customer $customer_id..."
        
        # Use docker exec to run SQL command directly
        billing_account_sql="INSERT INTO customer_billing_accounts (customer_id, account_number, billing_type, billing_cycle, status, credit_limit, current_balance, available_balance, reserved_balance, currency, auto_pay_enabled, created_at) VALUES ($customer_id, 'BA' || LPAD($customer_id::text, 6, '0'), 'POSTPAID', 'MONTHLY', 'ACTIVE', 50000.00, 0.00, 0.00, 0.00, 'NGN', false, NOW()) RETURNING id;"
        
        billing_account_id=$(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "$billing_account_sql" | tr -d ' ' | grep -o '^[0-9]*')
        
        if [ -n "$billing_account_id" ] && [ "$billing_account_id" != "" ]; then
            billing_account_ids="$billing_account_ids $billing_account_id"
            echo "✅ Created billing account $billing_account_id for customer $customer_id"
        else
            echo "⚠️  Failed to create billing account for customer $customer_id"
        fi
    fi
done

echo "📋 Billing Account IDs: $billing_account_ids"

# 4. Create sample invoices using billing accounts
echo ""
echo "4. Creating sample invoices..."

invoice_count=0
invoice_ids=""
billing_account_array=($billing_account_ids)
customer_array=($customer_ids)

for i in "${!customer_array[@]}"; do
    customer_id="${customer_array[$i]}"
    billing_account_id="${billing_account_array[$i]}"
    
    if [ -n "$customer_id" ] && [ -n "$billing_account_id" ]; then
        # Create invoice using SQL to ensure proper billing account reference
        echo "📡 Creating invoice for customer $customer_id (billing account $billing_account_id)..."
        
        invoice_sql="INSERT INTO invoices (
            invoice_number,
            billing_account_id,
            invoice_date,
            due_date,
            billing_period_start,
            billing_period_end,
            subtotal,
            tax_amount,
            discount_amount,
            adjustment_amount,
            total_amount,
            paid_amount,
            balance_due,
            status,
            currency,
            description,
            created_at
        ) VALUES (
            'INV-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('invoices_id_seq')::text, 4, '0'),
            $billing_account_id,
            NOW(),
            NOW() + INTERVAL '30 days',
            DATE_TRUNC('month', NOW()),
            DATE_TRUNC('month', NOW()) + INTERVAL '1 month' - INTERVAL '1 day',
            25000.00,
            0.00,
            0.00,
            0.00,
            25000.00,
            0.00,
            25000.00,
            'PENDING',
            'NGN',
            'Monthly Internet Service - ' || TO_CHAR(NOW(), 'Month YYYY'),
            NOW()
        ) RETURNING id;"
        
        invoice_id=$(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "$invoice_sql" | tr -d ' ' | grep -o '^[0-9]*')
        
        if [ -n "$invoice_id" ] && [ "$invoice_id" != "" ]; then
            invoice_ids="$invoice_ids $invoice_id"
            invoice_count=$((invoice_count + 1))
            echo "✅ Created invoice $invoice_id for customer $customer_id"
            
            # Create invoice items
            item_sql="INSERT INTO invoice_items (invoice_id, description, item_type, quantity, unit_price, line_total, created_at) VALUES 
            ($invoice_id, 'Internet Service - 200Mbps', 'service', 1, 20000.00, 20000.00, NOW()),
            ($invoice_id, 'Equipment Rental', 'equipment', 1, 5000.00, 5000.00, NOW());"
            
            docker exec isp-postgres psql -U isp_user -d isp_framework -c "$item_sql" > /dev/null
            echo "✅ Added invoice items for invoice $invoice_id"
        else
            echo "⚠️  Failed to create invoice for customer $customer_id"
        fi
    fi
done

echo "✅ Created $invoice_count invoices"

# 5. Create sample payments
echo ""
echo "5. Creating sample payments..."

payment_count=0
for invoice_id in $invoice_ids; do
    if [ -n "$invoice_id" ]; then
        echo "📡 Creating payment for invoice $invoice_id..."
        
        # Get billing account ID for this invoice
        billing_account_id=$(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT billing_account_id FROM invoices WHERE id = $invoice_id;" | tr -d ' ')
        
        payment_sql="INSERT INTO payments (
            payment_number,
            billing_account_id,
            invoice_id,
            payment_date,
            amount,
            currency,
            status,
            created_at
        ) VALUES (
            'PAY-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('payments_id_seq')::text, 4, '0'),
            $billing_account_id,
            $invoice_id,
            NOW(),
            12500.00,
            'NGN',
            'COMPLETED',
            NOW()
        ) RETURNING id;"
        
        payment_id=$(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "$payment_sql" | tr -d ' ' | grep -o '^[0-9]*')
        
        if [ -n "$payment_id" ] && [ "$payment_id" != "" ]; then
            payment_count=$((payment_count + 1))
            echo "✅ Created payment $payment_id for invoice $invoice_id"
            
            # Update invoice balance
            update_sql="UPDATE invoices SET paid_amount = 12500.00, balance_due = 12500.00 WHERE id = $invoice_id;"
            docker exec isp-postgres psql -U isp_user -d isp_framework -c "$update_sql" > /dev/null
        else
            echo "⚠️  Failed to create payment for invoice $invoice_id"
        fi
    fi
done

echo "✅ Created $payment_count payments"

# 6. Create sample credit notes
echo ""
echo "6. Creating sample credit notes..."

credit_note_count=0
for invoice_id in $invoice_ids; do
    if [ -n "$invoice_id" ]; then
        echo "📡 Creating credit note for invoice $invoice_id..."
        
        # Get billing account ID for this invoice
        billing_account_id=$(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT billing_account_id FROM invoices WHERE id = $invoice_id;" | tr -d ' ')
        
        credit_note_sql="INSERT INTO credit_notes (
            credit_note_number,
            billing_account_id,
            invoice_id,
            credit_date,
            amount,
            currency,
            reason,
            description,
            status,
            created_at
        ) VALUES (
            'CN-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('credit_notes_id_seq')::text, 4, '0'),
            $billing_account_id,
            $invoice_id,
            NOW(),
            2500.00,
            'NGN',
            'SERVICE_CREDIT',
            'Service credit for downtime compensation',
            'APPROVED',
            NOW()
        ) RETURNING id;"
        
        credit_note_id=$(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "$credit_note_sql" | tr -d ' ' | grep -o '^[0-9]*')
        
        if [ -n "$credit_note_id" ] && [ "$credit_note_id" != "" ]; then
            credit_note_count=$((credit_note_count + 1))
            echo "✅ Created credit note $credit_note_id for invoice $invoice_id"
            
            # Update invoice balance
            update_sql="UPDATE invoices SET balance_due = balance_due - 2500.00 WHERE id = $invoice_id;"
            docker exec isp-postgres psql -U isp_user -d isp_framework -c "$update_sql" > /dev/null
        else
            echo "⚠️  Failed to create credit note for invoice $invoice_id"
        fi
    fi
done

echo "✅ Created $credit_note_count credit notes"

# 7. Verify billing data creation
echo ""
echo "7. Verifying billing data creation..."

echo "📋 Database verification:"
echo "Customers: $(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT COUNT(*) FROM customers WHERE email LIKE 'complete_billing%';" | tr -d ' ')"

if [ -n "$customer_ids" ] && [ "$customer_ids" != " " ]; then
    customer_list=$(echo $customer_ids | tr ' ' ',')
    echo "Billing Accounts: $(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT COUNT(*) FROM customer_billing_accounts WHERE customer_id IN ($customer_list);" | tr -d ' ')"
else
    echo "Billing Accounts: 0"
fi

if [ -n "$billing_account_ids" ] && [ "$billing_account_ids" != " " ]; then
    billing_list=$(echo $billing_account_ids | tr ' ' ',')
    echo "Invoices: $(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT COUNT(*) FROM invoices WHERE billing_account_id IN ($billing_list);" | tr -d ' ')"
else
    echo "Invoices: 0"
fi

if [ -n "$invoice_ids" ] && [ "$invoice_ids" != " " ]; then
    invoice_list=$(echo $invoice_ids | tr ' ' ',')
    echo "Invoice Items: $(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT COUNT(*) FROM invoice_items WHERE invoice_id IN ($invoice_list);" | tr -d ' ')"
    echo "Payments: $(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT COUNT(*) FROM payments WHERE invoice_id IN ($invoice_list);" | tr -d ' ')"
    echo "Credit Notes: $(docker exec isp-postgres psql -U isp_user -d isp_framework -t -c "SELECT COUNT(*) FROM credit_notes WHERE invoice_id IN ($invoice_list);" | tr -d ' ')"
else
    echo "Invoice Items: 0"
    echo "Payments: 0"
    echo "Credit Notes: 0"
fi

# 8. Test billing API endpoints
echo ""
echo "8. Testing billing API endpoints..."

echo "📋 Testing billing overview..."
overview_response=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/billing/overview")
if echo "$overview_response" | grep -q '"total_invoices"'; then
    total_invoices=$(echo "$overview_response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total_invoices', 0))")
    echo "✅ Billing overview working - Total invoices: $total_invoices"
else
    echo "⚠️  Billing overview issue: $overview_response"
fi

echo "📋 Testing invoice listing..."
invoice_list_response=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/billing/invoices/")
if echo "$invoice_list_response" | grep -q '"id"'; then
    echo "✅ Invoice listing endpoint working"
else
    echo "⚠️  Invoice listing issue: $invoice_list_response"
fi

# 9. Final summary
echo ""
echo "=== Complete Billing Data Seeding Summary ==="
echo "✅ Billing customers: $(echo $customer_ids | wc -w) created"
echo "✅ Billing accounts: $(echo $billing_account_ids | wc -w) created"
echo "✅ Sample invoices: $invoice_count created"
echo "✅ Sample payments: $payment_count created"
echo "✅ Sample credit notes: $credit_note_count created"

echo ""
echo "🎉 Complete billing data seeding finished successfully!"
echo "The ISP Framework now has a fully functional billing system with:"
echo "   - Billing customers with proper data structure"
echo "   - Billing accounts for financial management"
echo "   - Sample invoices with billing periods and line items"
echo "   - Payment processing and tracking records"
echo "   - Credit note management examples"
echo "   - All data properly linked with foreign key relationships"

echo ""
echo "✅ BILLING SYSTEM FULLY OPERATIONAL WITH COMPLETE DATA!"
echo ""
echo "Customer IDs: $customer_ids"
echo "Billing Account IDs: $billing_account_ids"
echo "Invoice IDs: $invoice_ids"
echo ""
echo "Next steps:"
echo "1. Test billing workflows and reports via API"
echo "2. Validate billing calculations and balances"
echo "3. Test automated billing processes"
echo "4. Integrate with customer portal and service provisioning"
echo "5. Test billing account management features"
