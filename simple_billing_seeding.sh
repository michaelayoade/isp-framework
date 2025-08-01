#!/bin/bash

# ISP Framework - Simple Billing Data Seeding Script
# Creates invoices, payments, and credit notes directly using available endpoints

set -e

BASE_URL="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "🚀 Starting Simple Billing Data Seeding..."
echo "=========================================="

# Function to make authenticated API calls
make_api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local description="$4"
    
    echo "📡 $description..."
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Authorization: Bearer $JWT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" =~ ^2[0-9][0-9]$ ]]; then
        echo "✅ $description successful (HTTP $http_code)"
        return 0
    else
        echo "⚠️  $description failed (HTTP $http_code): $body"
        return 1
    fi
}

# 1. Authenticate as admin
echo "1. Authenticating as administrator..."
auth_response=$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USERNAME\",\"password\":\"$ADMIN_PASSWORD\"}" \
    "$BASE_URL/auth/login")

auth_http_code=$(echo "$auth_response" | tail -n1)
auth_body=$(echo "$auth_response" | head -n -1)

if [[ "$auth_http_code" =~ ^2[0-9][0-9]$ ]]; then
    JWT_TOKEN=$(echo "$auth_body" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Admin authentication successful"
else
    echo "❌ Admin authentication failed (HTTP $auth_http_code): $auth_body"
    exit 1
fi

# 2. Get existing customers
echo ""
echo "2. Retrieving existing customers..."
customers_response=$(make_api_call "GET" "/customers/" "" "Fetching customers")
if [ $? -ne 0 ]; then
    echo "❌ Failed to retrieve customers. Exiting."
    exit 1
fi

# Extract customer IDs
customer_ids=$(echo "$customers_response" | python3 -c "
import sys, json
try:
    lines = sys.stdin.read().strip().split('\n')
    for line in lines:
        if line.strip() and line.strip().startswith('{'):
            try:
                data = json.loads(line)
                if 'customers' in data:
                    customers = data['customers']
                    for customer in customers:
                        if 'id' in customer:
                            print(customer['id'])
                    break
            except json.JSONDecodeError:
                continue
except Exception as e:
    pass
")

if [ -z "$customer_ids" ]; then
    echo "⚠️  No customers found. Creating sample customers..."
    
    # Create sample customers
    for i in {1..5}; do
        customer_data="{
            \"name\": \"Billing Customer $i\",
            \"email\": \"billing$i@example.com\",
            \"phone\": \"+234801234567$i\",
            \"address\": \"$i Billing Street\",
            \"city\": \"Lagos\",
            \"country\": \"Nigeria\",
            \"postal_code\": \"20000$i\",
            \"status_id\": 1,
            \"reseller_id\": 1
        }"
        
        make_api_call "POST" "/customers/" "$customer_data" "Creating billing customer $i"
    done
    
    # Re-fetch customers
    customers_response=$(make_api_call "GET" "/customers/" "" "Re-fetching customers")
    customer_ids=$(echo "$customers_response" | python3 -c "
import sys, json
try:
    lines = sys.stdin.read().strip().split('\n')
    for line in lines:
        if line.strip() and line.strip().startswith('{'):
            try:
                data = json.loads(line)
                if 'customers' in data:
                    customers = data['customers']
                    for customer in customers:
                        if 'id' in customer:
                            print(customer['id'])
                    break
            except json.JSONDecodeError:
                continue
except Exception as e:
    pass
")
fi

if [ -z "$customer_ids" ]; then
    echo "❌ Failed to find or create customers. Exiting."
    exit 1
fi

echo "📋 Found customers with IDs: $(echo $customer_ids | tr '\n' ' ')"

# 3. Create sample invoices for each customer
echo ""
echo "3. Creating sample invoices..."

invoice_count=0
created_invoice_ids=""

for customer_id in $customer_ids; do
    # Create a monthly service invoice
    invoice_data="{
        \"customer_id\": $customer_id,
        \"amount\": 15000.00,
        \"currency\": \"NGN\",
        \"due_date\": \"$(date -d '+30 days' '+%Y-%m-%d')\",
        \"billing_period_start\": \"$(date -d '-30 days' '+%Y-%m-%d')\",
        \"billing_period_end\": \"$(date '+%Y-%m-%d')\",
        \"description\": \"Monthly Internet Service - $(date '+%B %Y')\",
        \"items\": [
            {
                \"description\": \"Internet Service - 100Mbps\",
                \"quantity\": 1,
                \"unit_price\": 12000.00,
                \"total_price\": 12000.00
            },
            {
                \"description\": \"Equipment Rental\",
                \"quantity\": 1,
                \"unit_price\": 3000.00,
                \"total_price\": 3000.00
            }
        ]
    }"
    
    invoice_response=$(make_api_call "POST" "/billing/invoices/" "$invoice_data" "Creating invoice for customer $customer_id")
    if [ $? -eq 0 ]; then
        invoice_count=$((invoice_count + 1))
        
        # Extract invoice ID
        invoice_id=$(echo "$invoice_response" | python3 -c "
import sys, json
try:
    lines = sys.stdin.read().strip().split('\n')
    for line in lines:
        if line.strip() and line.strip().startswith('{'):
            try:
                data = json.loads(line)
                if 'id' in data:
                    print(data['id'])
                    break
            except json.JSONDecodeError:
                continue
except:
    pass
")
        
        if [ -n "$invoice_id" ]; then
            created_invoice_ids="$created_invoice_ids $invoice_id"
        fi
    fi
    
    # Limit to first 5 customers for demo
    if [ $invoice_count -ge 5 ]; then
        break
    fi
done

echo "✅ Created $invoice_count invoices"

# 4. Create sample payments for invoices
echo ""
echo "4. Creating sample payments..."

payment_count=0
for invoice_id in $created_invoice_ids; do
    if [ -n "$invoice_id" ]; then
        payment_data="{
            \"invoice_id\": $invoice_id,
            \"amount\": 7500.00,
            \"currency\": \"NGN\",
            \"payment_method\": \"bank_transfer\",
            \"payment_date\": \"$(date '+%Y-%m-%d')\",
            \"reference\": \"PAY$(date +%s)$invoice_id\",
            \"notes\": \"Partial payment via bank transfer\"
        }"
        
        make_api_call "POST" "/billing/payments/" "$payment_data" "Creating payment for invoice $invoice_id"
        if [ $? -eq 0 ]; then
            payment_count=$((payment_count + 1))
        fi
    fi
done

echo "✅ Created $payment_count payments"

# 5. Create sample credit notes for invoices
echo ""
echo "5. Creating sample credit notes..."

credit_note_count=0
for invoice_id in $created_invoice_ids; do
    if [ -n "$invoice_id" ]; then
        credit_note_data="{
            \"invoice_id\": $invoice_id,
            \"amount\": 1500.00,
            \"currency\": \"NGN\",
            \"reason\": \"service_credit\",
            \"description\": \"Service credit for downtime compensation\",
            \"credit_date\": \"$(date '+%Y-%m-%d')\"
        }"
        
        make_api_call "POST" "/billing/credit-notes/" "$credit_note_data" "Creating credit note for invoice $invoice_id"
        if [ $? -eq 0 ]; then
            credit_note_count=$((credit_note_count + 1))
        fi
    fi
done

echo "✅ Created $credit_note_count credit notes"

# 6. Test billing overview
echo ""
echo "6. Testing billing overview..."
overview_response=$(make_api_call "GET" "/billing/overview" "" "Testing billing overview endpoint")

# 7. List all created billing data
echo ""
echo "7. Listing created billing data..."

echo "📋 Listing invoices..."
make_api_call "GET" "/billing/invoices/" "" "Listing all invoices"

echo ""
echo "📋 Listing payments..."
make_api_call "GET" "/billing/payments/" "" "Listing all payments"

echo ""
echo "📋 Listing credit notes..."
make_api_call "GET" "/billing/credit-notes/" "" "Listing all credit notes"

# 8. Final summary
echo ""
echo "=== Simple Billing Data Seeding Summary ==="
echo "✅ Sample invoices: $invoice_count created"
echo "✅ Sample payments: $payment_count created"
echo "✅ Sample credit notes: $credit_note_count created"

echo ""
echo "🎉 Simple billing data seeding completed successfully!"
echo "The ISP Framework now has comprehensive billing test data:"
echo "   - Sample invoices with billing periods and line items"
echo "   - Payment processing and tracking records"
echo "   - Credit note management examples"
echo "   - Billing overview functionality tested"

echo ""
echo "✅ BILLING SYSTEM DATA SEEDING COMPLETE!"
echo ""
echo "Next steps:"
echo "1. Test billing workflows and reports"
echo "2. Validate billing calculations and balances"
echo "3. Test automated billing processes"
echo "4. Integrate with customer portal and service provisioning"
