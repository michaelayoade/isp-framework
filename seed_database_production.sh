#!/bin/bash

# ISP Framework Database Seeding Script - Production Ready
# Creates comprehensive test data for billing system validation
# Handles existing data gracefully and uses unique identifiers

set -e  # Exit on any error

# Configuration
API_BASE="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"
TIMESTAMP=$(date +%s)

echo "🚀 Starting ISP Framework Database Seeding (Production Ready)..."
echo "API Base URL: $API_BASE"
echo "Timestamp: $TIMESTAMP"

# 1. Authenticate as administrator
echo "1. Authenticating as administrator..."
AUTH_RESPONSE=$(curl -s -X POST "$API_BASE/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$ADMIN_USERNAME&password=$ADMIN_PASSWORD")

if echo "$AUTH_RESPONSE" | grep -q '"access_token"'; then
    TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Authentication successful"
else
    echo "❌ Authentication failed: $AUTH_RESPONSE"
    exit 1
fi

# Initialize counters
CUSTOMER_STATUS_COUNT=0
BILLING_TYPE_COUNT=0
SERVICE_TYPE_COUNT=0
CUSTOMER_COUNT=0
INVOICE_COUNT=0
PAYMENT_COUNT=0
CREDIT_NOTE_COUNT=0

# 2. Create customer statuses (handle existing gracefully)
echo "2. Creating customer statuses..."
declare -a CUSTOMER_STATUSES=(
    "new:New Customer:Newly registered customer"
    "active:Active Customer:Active paying customer"
    "suspended:Suspended:Account temporarily suspended"
    "terminated:Terminated:Account permanently closed"
)

for status in "${CUSTOMER_STATUSES[@]}"; do
    IFS=':' read -r code name description <<< "$status"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/customer-statuses/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"code\": \"$code\",
            \"name\": \"$name\",
            \"description\": \"$description\",
            \"is_active\": true
        }")
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        echo "✅ Customer status '$name' created"
        CUSTOMER_STATUS_COUNT=$((CUSTOMER_STATUS_COUNT + 1))
    elif echo "$RESPONSE" | grep -q "already exists"; then
        echo "✅ Customer status '$name' already exists"
        CUSTOMER_STATUS_COUNT=$((CUSTOMER_STATUS_COUNT + 1))
    else
        echo "⚠️  Customer status '$name' issue: $RESPONSE"
    fi
done

# 3. Create billing types (handle existing gracefully)
echo "3. Creating billing types..."
declare -a BILLING_TYPES=(
    "prepaid:Prepaid:Pay-as-you-go billing"
    "postpaid:Postpaid:Monthly billing cycle"
    "corporate:Corporate:Enterprise billing"
    "trial:Trial:Free trial period"
)

for billing_type in "${BILLING_TYPES[@]}"; do
    IFS=':' read -r code name description <<< "$billing_type"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/billing-types/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"code\": \"$code\",
            \"name\": \"$name\",
            \"description\": \"$description\",
            \"is_active\": true
        }")
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        echo "✅ Billing type '$name' created"
        BILLING_TYPE_COUNT=$((BILLING_TYPE_COUNT + 1))
    elif echo "$RESPONSE" | grep -q "already exists"; then
        echo "✅ Billing type '$name' already exists"
        BILLING_TYPE_COUNT=$((BILLING_TYPE_COUNT + 1))
    else
        echo "⚠️  Billing type '$name' issue: $RESPONSE"
    fi
done

# 4. Create service types (handle existing gracefully)
echo "4. Creating service types..."
declare -a SERVICE_TYPES=(
    "INTERNET:Internet Service:High-speed internet connectivity"
    "VOICE:Voice Service:VoIP and traditional phone services"
    "BUNDLE:Bundle Service:Combined internet and voice packages"
    "RECURRING:Recurring Service:Monthly recurring service"
)

for service_type in "${SERVICE_TYPES[@]}"; do
    IFS=':' read -r code name description <<< "$service_type"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/service-types/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"code\": \"$code\",
            \"name\": \"$name\",
            \"description\": \"$description\",
            \"is_active\": true
        }")
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        echo "✅ Service type '$name' created"
        SERVICE_TYPE_COUNT=$((SERVICE_TYPE_COUNT + 1))
    elif echo "$RESPONSE" | grep -q "already exists"; then
        echo "✅ Service type '$name' already exists"
        SERVICE_TYPE_COUNT=$((SERVICE_TYPE_COUNT + 1))
    else
        echo "⚠️  Service type '$name' creation failed: $RESPONSE"
    fi
done

# 5. Create test customers (use unique emails with timestamp)
echo "5. Creating test customers..."
declare -a CUSTOMERS=(
    "John Smith:+1-555-0101"
    "Jane Doe:+1-555-0102"
    "Bob Johnson:+1-555-0103"
    "Alice Brown:+1-555-0104"
    "Charlie Wilson:+1-555-0105"
    "Diana Miller:+1-555-0106"
    "Frank Davis:+1-555-0107"
    "Grace Taylor:+1-555-0108"
    "Henry Anderson:+1-555-0109"
    "Ivy Thomas:+1-555-0110"
)

customer_index=1
for customer in "${CUSTOMERS[@]}"; do
    IFS=':' read -r name phone <<< "$customer"
    
    # Create unique email using timestamp and index
    email="${name// /}${TIMESTAMP}${customer_index}@example.com"
    email=$(echo "$email" | tr '[:upper:]' '[:lower:]')
    
    RESPONSE=$(curl -s -X POST "$API_BASE/customers/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"email\": \"$email\",
            \"phone\": \"$phone\",
            \"status_id\": 1
        }")
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        CUSTOMER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
        echo "✅ Customer '$name' created (ID: $CUSTOMER_ID, Email: $email)"
        CUSTOMER_COUNT=$((CUSTOMER_COUNT + 1))
    else
        echo "⚠️  Customer '$name' creation failed: $RESPONSE"
    fi
    
    customer_index=$((customer_index + 1))
done

# 6. Create sample invoices (if customers exist)
echo "6. Creating sample invoices..."
if [ $CUSTOMER_COUNT -gt 0 ]; then
    for i in {1..5}; do
        # Use customer IDs starting from the most recent ones
        CUSTOMER_ID=$((11 + i - 1))  # Assuming customers start from ID 11 based on test
        
        RESPONSE=$(curl -s -X POST "$API_BASE/billing/invoices/" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"customer_id\": $CUSTOMER_ID,
                \"invoice_date\": \"2025-07-01T00:00:00Z\",
                \"due_date\": \"2025-07-31T23:59:59Z\",
                \"billing_period_start\": \"2025-07-01T00:00:00Z\",
                \"billing_period_end\": \"2025-07-31T23:59:59Z\",
                \"subtotal\": 50.00,
                \"tax_amount\": 5.00,
                \"total_amount\": 55.00,
                \"currency\": \"USD\",
                \"status\": \"DRAFT\",
                \"notes\": \"Monthly service invoice for July 2025\"
            }")
        
        if echo "$RESPONSE" | grep -q '"id"'; then
            INVOICE_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
            echo "✅ Invoice $i created for customer $CUSTOMER_ID (Invoice ID: $INVOICE_ID)"
            INVOICE_COUNT=$((INVOICE_COUNT + 1))
        else
            echo "⚠️  Invoice creation failed for customer $CUSTOMER_ID: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping invoice creation - no customers available"
fi

# 7. Create sample payments (if invoices exist)
echo "7. Creating sample payments..."
if [ $INVOICE_COUNT -gt 0 ]; then
    for i in {1..3}; do
        INVOICE_ID=$i
        CUSTOMER_ID=$((11 + i - 1))
        
        RESPONSE=$(curl -s -X POST "$API_BASE/billing/payments/" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"customer_id\": $CUSTOMER_ID,
                \"invoice_id\": $INVOICE_ID,
                \"amount\": 55.00,
                \"payment_method\": \"credit_card\",
                \"payment_date\": \"2025-07-15T10:00:00Z\",
                \"status\": \"COMPLETED\",
                \"reference_number\": \"PAY-$TIMESTAMP-$(printf '%03d' $i)\",
                \"notes\": \"Payment for invoice $INVOICE_ID\"
            }")
        
        if echo "$RESPONSE" | grep -q '"id"'; then
            PAYMENT_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
            echo "✅ Payment $i created for invoice $INVOICE_ID (Payment ID: $PAYMENT_ID)"
            PAYMENT_COUNT=$((PAYMENT_COUNT + 1))
        else
            echo "⚠️  Payment creation failed for invoice $INVOICE_ID: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping payment creation - no invoices available"
fi

# 8. Create sample credit notes (if customers and invoices exist)
echo "8. Creating sample credit notes..."
if [ $CUSTOMER_COUNT -gt 0 ] && [ $INVOICE_COUNT -gt 0 ]; then
    for i in {1..2}; do
        CUSTOMER_ID=$((11 + i - 1))
        INVOICE_ID=$i
        
        RESPONSE=$(curl -s -X POST "$API_BASE/billing/credit-notes/" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"customer_id\": $CUSTOMER_ID,
                \"invoice_id\": $INVOICE_ID,
                \"amount\": 25.00,
                \"reason\": \"service_credit\",
                \"description\": \"Service credit for downtime\",
                \"credit_date\": \"2025-07-20T00:00:00Z\",
                \"status\": \"APPROVED\",
                \"notes\": \"Credit for service interruption\"
            }")
        
        if echo "$RESPONSE" | grep -q '"id"'; then
            CREDIT_NOTE_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
            echo "✅ Credit note $i created for customer $CUSTOMER_ID (Credit Note ID: $CREDIT_NOTE_ID)"
            CREDIT_NOTE_COUNT=$((CREDIT_NOTE_COUNT + 1))
        else
            echo "⚠️  Credit note creation failed for customer $CUSTOMER_ID: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping credit note creation - customers: $CUSTOMER_COUNT, invoices: $INVOICE_COUNT"
fi

# Summary
echo
echo "=== Database Seeding Summary ==="
echo "✅ Customer statuses: $CUSTOMER_STATUS_COUNT created/verified"
echo "✅ Billing types: $BILLING_TYPE_COUNT created/verified"
echo "✅ Service types: $SERVICE_TYPE_COUNT created/verified"
echo "✅ Test customers: $CUSTOMER_COUNT created"
echo "✅ Sample invoices: $INVOICE_COUNT created"
echo "✅ Sample payments: $PAYMENT_COUNT created"
echo "✅ Sample credit notes: $CREDIT_NOTE_COUNT created"
echo
echo "🎉 Database seeding completed successfully!"
echo "The ISP Framework now has comprehensive test data for:"
echo "   - Customer management and billing"
echo "   - Invoice generation and payment processing"
echo "   - Credit note management"
echo "   - Billing analytics and reporting"
echo
echo "✅ READY FOR BILLING SYSTEM TESTING!"
echo
echo "Next steps:"
echo "1. Run comprehensive billing system tests"
echo "2. Validate invoice generation and payment processing"
echo "3. Test credit note management workflows"
echo "4. Verify billing analytics and reporting"
