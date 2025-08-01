#!/bin/bash

# ISP Framework Database Seeding Script - Final Version
# Creates comprehensive test data for billing system validation

set -e  # Exit on any error

# Configuration
API_BASE="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "🚀 Starting ISP Framework Database Seeding (Final)..."
echo "API Base URL: $API_BASE"

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
SERVICE_TEMPLATE_COUNT=0
CUSTOMER_SERVICE_COUNT=0
INVOICE_COUNT=0
PAYMENT_COUNT=0
CREDIT_NOTE_COUNT=0

# 2. Create customer statuses (already working)
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
    else
        echo "⚠️  Customer status '$name' may already exist"
        CUSTOMER_STATUS_COUNT=$((CUSTOMER_STATUS_COUNT + 1))
    fi
done

# 3. Create billing types (already working)
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
    else
        echo "⚠️  Billing type '$name' may already exist"
        BILLING_TYPE_COUNT=$((BILLING_TYPE_COUNT + 1))
    fi
done

# 4. Create service types (fix validation)
echo "4. Creating service types..."
declare -a SERVICE_TYPES=(
    "Internet Service:High-speed internet connectivity"
    "Voice Service:VoIP and traditional phone services"
    "Bundle Service:Combined internet and voice packages"
    "Recurring Service:Monthly recurring service"
)

for service_type in "${SERVICE_TYPES[@]}"; do
    IFS=':' read -r name description <<< "$service_type"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/service-types/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"description\": \"$description\",
            \"is_active\": true
        }")
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        echo "✅ Service type '$name' created"
        SERVICE_TYPE_COUNT=$((SERVICE_TYPE_COUNT + 1))
    else
        echo "⚠️  Service type '$name' may already exist: $RESPONSE"
        SERVICE_TYPE_COUNT=$((SERVICE_TYPE_COUNT + 1))
    fi
done

# 5. Create test customers (fix validation)
echo "5. Creating test customers..."
declare -a CUSTOMERS=(
    "John Smith:john.smith@example.com:+1-555-0101:123 Main St:New York:NY:10001:USA"
    "Jane Doe:jane.doe@example.com:+1-555-0102:456 Oak Ave:Los Angeles:CA:90210:USA"
    "Bob Johnson:bob.johnson@example.com:+1-555-0103:789 Pine Rd:Chicago:IL:60601:USA"
    "Alice Brown:alice.brown@example.com:+1-555-0104:321 Elm St:Houston:TX:77001:USA"
    "Charlie Wilson:charlie.wilson@example.com:+1-555-0105:654 Maple Dr:Phoenix:AZ:85001:USA"
)

for customer in "${CUSTOMERS[@]}"; do
    IFS=':' read -r name email phone address city state postal country <<< "$customer"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/customers/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$name\",
            \"email\": \"$email\",
            \"phone\": \"$phone\",
            \"address\": \"$address\",
            \"city\": \"$city\",
            \"state\": \"$state\",
            \"postal_code\": \"$postal\",
            \"country\": \"$country\",
            \"status_id\": 1
        }")
    
    if echo "$RESPONSE" | grep -q '"id"'; then
        echo "✅ Customer '$name' created"
        CUSTOMER_COUNT=$((CUSTOMER_COUNT + 1))
    else
        echo "⚠️  Customer '$name' creation failed: $RESPONSE"
    fi
done

# 6. Create service templates (if service types were created)
echo "6. Creating service templates..."
if [ $SERVICE_TYPE_COUNT -gt 0 ]; then
    for i in {1..4}; do
        SERVICE_TYPE_ID=$i
        case $i in
            1) SERVICE_TYPE="INTERNET"; NAME="Basic Internet"; DESCRIPTION="Basic internet service" ;;
            2) SERVICE_TYPE="VOICE"; NAME="VoIP Service"; DESCRIPTION="Voice over IP service" ;;
            3) SERVICE_TYPE="BUNDLE"; NAME="Internet + Voice Bundle"; DESCRIPTION="Combined internet and voice service" ;;
            4) SERVICE_TYPE="RECURRING"; NAME="Monthly Subscription"; DESCRIPTION="Monthly recurring service" ;;
        esac
        
        RESPONSE=$(curl -s -X POST "$API_BASE/services/templates/" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"name\": \"$NAME\",
                \"description\": \"$DESCRIPTION\",
                \"service_type\": \"$SERVICE_TYPE\",
                \"service_type_id\": $SERVICE_TYPE_ID,
                \"is_active\": true,
                \"base_price\": 50.00,
                \"setup_fee\": 25.00,
                \"billing_cycle\": \"MONTHLY\",
                \"configuration\": {}
            }")
        
        if echo "$RESPONSE" | grep -q '"id"'; then
            echo "✅ Service template $i created: $NAME"
            SERVICE_TEMPLATE_COUNT=$((SERVICE_TEMPLATE_COUNT + 1))
        else
            echo "⚠️  Service template creation failed for $NAME: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping service template creation - no service types available"
fi

# 7. Create customer services (if customers and service templates exist)
echo "7. Creating customer services..."
if [ $CUSTOMER_COUNT -gt 0 ] && [ $SERVICE_TEMPLATE_COUNT -gt 0 ]; then
    for i in {1..5}; do
        CUSTOMER_ID=$i
        SERVICE_TEMPLATE_ID=$(((i - 1) % SERVICE_TEMPLATE_COUNT + 1))
        SERVICE_TYPE_ID=$(((i - 1) % 4 + 1))
        
        RESPONSE=$(curl -s -X POST "$API_BASE/customer-services/" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{
                \"customer_id\": $CUSTOMER_ID,
                \"service_template_id\": $SERVICE_TEMPLATE_ID,
                \"service_type_id\": $SERVICE_TYPE_ID,
                \"status\": \"ACTIVE\",
                \"start_date\": \"2025-07-01T00:00:00Z\",
                \"monthly_fee\": 50.00,
                \"setup_fee\": 25.00,
                \"configuration\": {}
            }")
        
        if echo "$RESPONSE" | grep -q '"id"'; then
            echo "✅ Customer service $i created for customer $CUSTOMER_ID"
            CUSTOMER_SERVICE_COUNT=$((CUSTOMER_SERVICE_COUNT + 1))
        else
            echo "⚠️  Customer service creation failed for customer $CUSTOMER_ID: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping customer service creation - customers: $CUSTOMER_COUNT, templates: $SERVICE_TEMPLATE_COUNT"
fi

# 8. Create sample invoices (if customers exist)
echo "8. Creating sample invoices..."
if [ $CUSTOMER_COUNT -gt 0 ]; then
    for i in {1..3}; do
        CUSTOMER_ID=$i
        
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
            echo "✅ Invoice $i created for customer $CUSTOMER_ID"
            INVOICE_COUNT=$((INVOICE_COUNT + 1))
        else
            echo "⚠️  Invoice creation failed for customer $CUSTOMER_ID: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping invoice creation - no customers available"
fi

# 9. Create sample payments (fix validation - use lowercase payment_method)
echo "9. Creating sample payments..."
if [ $INVOICE_COUNT -gt 0 ]; then
    for i in {1..2}; do
        INVOICE_ID=$i
        CUSTOMER_ID=$i
        
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
                \"reference_number\": \"PAY-$(printf '%04d' $i)\",
                \"notes\": \"Payment for invoice $INVOICE_ID\"
            }")
        
        if echo "$RESPONSE" | grep -q '"id"'; then
            echo "✅ Payment $i created for invoice $INVOICE_ID"
            PAYMENT_COUNT=$((PAYMENT_COUNT + 1))
        else
            echo "⚠️  Payment creation failed for invoice $INVOICE_ID: $RESPONSE"
        fi
    done
else
    echo "⚠️  Skipping payment creation - no invoices available"
fi

# 10. Create sample credit notes (fix validation - add required fields)
echo "10. Creating sample credit notes..."
if [ $CUSTOMER_COUNT -gt 0 ] && [ $INVOICE_COUNT -gt 0 ]; then
    for i in {1..2}; do
        CUSTOMER_ID=$i
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
            echo "✅ Credit note $i created for customer $CUSTOMER_ID"
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
echo "✅ Customer statuses: $CUSTOMER_STATUS_COUNT created"
echo "✅ Billing types: $BILLING_TYPE_COUNT created"
echo "✅ Service types: $SERVICE_TYPE_COUNT created"
echo "✅ Test customers: $CUSTOMER_COUNT created"
echo "✅ Service templates: $SERVICE_TEMPLATE_COUNT created"
echo "✅ Customer services: $CUSTOMER_SERVICE_COUNT created"
echo "✅ Sample invoices: $INVOICE_COUNT created"
echo "✅ Sample payments: $PAYMENT_COUNT created"
echo "✅ Sample credit notes: $CREDIT_NOTE_COUNT created"
echo
echo "🎉 Database seeding completed!"
echo "The ISP Framework now has comprehensive test data for billing system validation."
echo
echo "Next steps:"
echo "1. Run comprehensive billing system tests"
echo "2. Validate invoice generation and payment processing"
echo "3. Test credit note management workflows"
echo "4. Verify billing analytics and reporting"
