#!/bin/bash

# Simple Customer Creation Test Script
# Tests customer creation with minimal data to isolate the issue

set -e

API_BASE="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "🔍 Testing Customer Creation Issue..."

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

# 2. Test minimal customer creation
echo "2. Testing minimal customer creation..."
RESPONSE=$(curl -s -X POST "$API_BASE/customers/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Customer",
        "email": "test@example.com",
        "status_id": 1
    }')

echo "Response: $RESPONSE"

if echo "$RESPONSE" | grep -q '"id"'; then
    echo "✅ Customer creation successful"
    CUSTOMER_ID=$(echo "$RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "Customer ID: $CUSTOMER_ID"
else
    echo "❌ Customer creation failed"
    echo "Error details: $RESPONSE"
fi

# 3. Test with even more minimal data
echo "3. Testing with absolutely minimal data..."
RESPONSE2=$(curl -s -X POST "$API_BASE/customers/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Minimal Test",
        "status_id": 1
    }')

echo "Minimal Response: $RESPONSE2"

if echo "$RESPONSE2" | grep -q '"id"'; then
    echo "✅ Minimal customer creation successful"
else
    echo "❌ Minimal customer creation failed"
fi
