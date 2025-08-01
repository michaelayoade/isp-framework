#!/bin/bash

# ISP Framework - Final Billing Data Seeding Script
# Creates comprehensive billing test data using direct API calls

set -e

BASE_URL="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "🚀 Starting Final Billing Data Seeding..."
echo "========================================"

# 1. Authenticate as admin
echo "1. Authenticating as administrator..."
auth_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}" \
    "$BASE_URL/auth/login")

JWT_TOKEN=$(echo "$auth_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Admin authentication successful"

# 2. Create billing customers with known IDs
echo ""
echo "2. Creating billing customers..."

customer_ids=""
for i in {1..3}; do
    customer_data="{
        \"name\": \"Billing Test Customer $i\",
        \"email\": \"billing_test$i@example.com\",
        \"phone\": \"+234901234567$i\",
        \"address\": \"$i Test Billing Street\",
        \"city\": \"Lagos\",
        \"country\": \"Nigeria\",
        \"postal_code\": \"30000$i\",
        \"status_id\": 1,
        \"reseller_id\": 1
    }"
    
    echo "📡 Creating billing customer $i..."
    customer_response=$(curl -s -X POST \
        -H "Authorization: Bearer $JWT_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$customer_data" \
        "$BASE_URL/customers/")
    
    # Extract customer ID from response
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
        echo "⚠️  Failed to extract customer ID for customer $i"
    fi
done

echo "📋 Customer IDs: $customer_ids"

# 3. Create sample invoices
echo ""
echo "3. Creating sample invoices..."

invoice_count=0
invoice_ids=""

for customer_id in $customer_ids; do
    if [ -n "$customer_id" ]; then
        invoice_data="{
            \"customer_id\": $customer_id,
            \"amount\": 25000.00,
            \"currency\": \"NGN\",
            \"invoice_date\": \"$(date '+%Y-%m-%dT%H:%M:%S')\",
            \"due_date\": \"$(date -d '+30 days' '+%Y-%m-%dT%H:%M:%S')\",
            \"billing_period_start\": \"$(date -d '-30 days' '+%Y-%m-%dT%H:%M:%S')\",
            \"billing_period_end\": \"$(date '+%Y-%m-%dT%H:%M:%S')\",
            \"description\": \"Monthly Internet Service - $(date '+%B %Y')\",
            \"items\": [
                {
                    \"description\": \"Internet Service - 200Mbps\",
                    \"quantity\": 1,
                    \"unit_price\": 20000.00,
                    \"total_price\": 20000.00
                },
                {
                    \"description\": \"Equipment Rental\",
                    \"quantity\": 1,
                    \"unit_price\": 5000.00,
                    \"total_price\": 5000.00
                }
            ]
        }"
        
        echo "📡 Creating invoice for customer $customer_id..."
        invoice_response=$(curl -s -X POST \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$invoice_data" \
            "$BASE_URL/billing/invoices/")
        
        # Check if invoice creation was successful
        if echo "$invoice_response" | grep -q '"id"'; then
            invoice_id=$(echo "$invoice_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'id' in data:
        print(data['id'])
except:
    pass
")
            if [ -n "$invoice_id" ]; then
                invoice_ids="$invoice_ids $invoice_id"
                invoice_count=$((invoice_count + 1))
                echo "✅ Created invoice $invoice_id for customer $customer_id"
            fi
        else
            echo "⚠️  Failed to create invoice for customer $customer_id"
            echo "Response: $invoice_response"
        fi
    fi
done

echo "✅ Created $invoice_count invoices"

# 4. Create sample payments
echo ""
echo "4. Creating sample payments..."

payment_count=0
for invoice_id in $invoice_ids; do
    if [ -n "$invoice_id" ]; then
        payment_data="{
            \"invoice_id\": $invoice_id,
            \"amount\": 12500.00,
            \"currency\": \"NGN\",
            \"payment_method\": \"bank_transfer\",
            \"payment_date\": \"$(date '+%Y-%m-%dT%H:%M:%S')\",
            \"reference\": \"PAY$(date +%s)$invoice_id\",
            \"notes\": \"Partial payment via bank transfer\"
        }"
        
        echo "📡 Creating payment for invoice $invoice_id..."
        payment_response=$(curl -s -X POST \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$payment_data" \
            "$BASE_URL/billing/payments/")
        
        if echo "$payment_response" | grep -q '"id"'; then
            payment_count=$((payment_count + 1))
            echo "✅ Created payment for invoice $invoice_id"
        else
            echo "⚠️  Failed to create payment for invoice $invoice_id"
            echo "Response: $payment_response"
        fi
    fi
done

echo "✅ Created $payment_count payments"

# 5. Create sample credit notes
echo ""
echo "5. Creating sample credit notes..."

credit_note_count=0
for invoice_id in $invoice_ids; do
    if [ -n "$invoice_id" ]; then
        credit_note_data="{
            \"invoice_id\": $invoice_id,
            \"amount\": 2500.00,
            \"currency\": \"NGN\",
            \"reason\": \"service_credit\",
            \"description\": \"Service credit for downtime compensation\",
            \"credit_date\": \"$(date '+%Y-%m-%dT%H:%M:%S')\"
        }"
        
        echo "📡 Creating credit note for invoice $invoice_id..."
        credit_note_response=$(curl -s -X POST \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$credit_note_data" \
            "$BASE_URL/billing/credit-notes/")
        
        if echo "$credit_note_response" | grep -q '"id"'; then
            credit_note_count=$((credit_note_count + 1))
            echo "✅ Created credit note for invoice $invoice_id"
        else
            echo "⚠️  Failed to create credit note for invoice $invoice_id"
            echo "Response: $credit_note_response"
        fi
    fi
done

echo "✅ Created $credit_note_count credit notes"

# 6. Test billing overview
echo ""
echo "6. Testing billing overview..."
overview_response=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/billing/overview")
if echo "$overview_response" | grep -q '"total"'; then
    echo "✅ Billing overview endpoint working"
else
    echo "⚠️  Billing overview endpoint issue: $overview_response"
fi

# 7. List all billing data
echo ""
echo "7. Listing created billing data..."

echo "📋 Invoices:"
curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/billing/invoices/" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'Found {len(data)} invoices')
    elif 'items' in data:
        print(f'Found {len(data[\"items\"])} invoices')
    elif 'invoices' in data:
        print(f'Found {len(data[\"invoices\"])} invoices')
    else:
        print('Invoice data structure:', list(data.keys()) if isinstance(data, dict) else type(data))
except Exception as e:
    print(f'Error parsing invoices: {e}')
"

echo "📋 Payments:"
curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/billing/payments/" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'Found {len(data)} payments')
    elif 'items' in data:
        print(f'Found {len(data[\"items\"])} payments')
    elif 'payments' in data:
        print(f'Found {len(data[\"payments\"])} payments')
    else:
        print('Payment data structure:', list(data.keys()) if isinstance(data, dict) else type(data))
except Exception as e:
    print(f'Error parsing payments: {e}')
"

echo "📋 Credit Notes:"
curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/billing/credit-notes/" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'Found {len(data)} credit notes')
    elif 'items' in data:
        print(f'Found {len(data[\"items\"])} credit notes')
    elif 'credit_notes' in data:
        print(f'Found {len(data[\"credit_notes\"])} credit notes')
    else:
        print('Credit note data structure:', list(data.keys()) if isinstance(data, dict) else type(data))
except Exception as e:
    print(f'Error parsing credit notes: {e}')
"

# 8. Final summary
echo ""
echo "=== Final Billing Data Seeding Summary ==="
echo "✅ Billing customers: $(echo $customer_ids | wc -w) created"
echo "✅ Sample invoices: $invoice_count created"
echo "✅ Sample payments: $payment_count created"
echo "✅ Sample credit notes: $credit_note_count created"

echo ""
echo "🎉 Final billing data seeding completed successfully!"
echo "The ISP Framework now has comprehensive billing test data:"
echo "   - Billing customers with proper data structure"
echo "   - Sample invoices with billing periods and line items"
echo "   - Payment processing and tracking records"
echo "   - Credit note management examples"
echo "   - Billing overview functionality tested"

echo ""
echo "✅ BILLING SYSTEM DATA SEEDING COMPLETE!"
echo ""
echo "Customer IDs created: $customer_ids"
echo "Invoice IDs created: $invoice_ids"
echo ""
echo "Next steps:"
echo "1. Test billing workflows and reports"
echo "2. Validate billing calculations and balances"
echo "3. Test automated billing processes"
echo "4. Integrate with customer portal and service provisioning"
