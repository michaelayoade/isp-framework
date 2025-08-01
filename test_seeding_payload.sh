#!/bin/bash

# Test the exact payload that's failing in the seeding script
API_BASE="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"
TIMESTAMP=$(date +%s)

echo "🔍 Testing Seeding Script Payload..."

# 1. Authenticate
echo "1. Authenticating..."
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

# 2. Test exact seeding script payload
echo "2. Testing exact seeding script payload..."
name="John Smith"
phone="+1-555-0101"
email="johnsmith${TIMESTAMP}1@example.com"

echo "Testing with:"
echo "  Name: $name"
echo "  Email: $email"
echo "  Phone: $phone"

RESPONSE=$(curl -s -X POST "$API_BASE/customers/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"$name\",
        \"email\": \"$email\",
        \"phone\": \"$phone\",
        \"status_id\": 1
    }")

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q '"id"'; then
    CUSTOMER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "✅ Customer creation successful (ID: $CUSTOMER_ID)"
else
    echo "❌ Customer creation failed"
    echo "Error details: $RESPONSE"
fi
