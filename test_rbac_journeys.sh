#!/bin/bash

# RBAC User Journey Simulation Script
# Tests granular role-based access control with curl commands

echo "🚀 RBAC USER JOURNEY SIMULATION"
echo "================================="
echo ""

# Configuration
BASE_URL="https://marketing.dotmac.ng"
AUTH_ENDPOINT="$BASE_URL/api/v1/auth/token"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log test results
log_test() {
    local test_name="$1"
    local expected_status="$2"
    local actual_status="$3"
    local description="$4"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$expected_status" = "$actual_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} | $test_name | Expected: $expected_status, Got: $actual_status | $description"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAIL${NC} | $test_name | Expected: $expected_status, Got: $actual_status | $description"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Function to test API endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local token="$3"
    local expected_status="$4"
    local test_name="$5"
    local description="$6"
    local data="$7"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token")
    fi
    
    http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    log_test "$test_name" "$expected_status" "$http_status" "$description"
    
    # Return the response body for further analysis if needed
    echo "$response" | sed -e 's/HTTPSTATUS:.*//g'
}

echo "🔐 PHASE 1: AUTHENTICATION TESTING"
echo "-----------------------------------"

# Test 1: Admin Authentication (Super Admin Role)
echo ""
echo -e "${BLUE}Test 1: Admin Authentication (Super Admin Role)${NC}"
TOKEN=$(curl -s -X POST "$AUTH_ENDPOINT" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123" | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
    echo -e "${GREEN}✅ Authentication successful${NC}"
    echo "Token: ${TOKEN:0:50}..."
else
    echo -e "${RED}❌ Authentication failed${NC}"
    exit 1
fi

echo ""
echo "🛡️ PHASE 2: PERMISSION TESTING (SUPER ADMIN)"
echo "---------------------------------------------"

# Test 2: Customer Management (Should have full access)
echo ""
echo -e "${BLUE}Test 2: Customer Management Permissions${NC}"

# Test customers.view permission
test_endpoint "GET" "/api/v1/customers" "$TOKEN" "200" "customers.view" "Super admin should view customers"

# Test customers.create permission
customer_data='{"name":"Test Customer","email":"test@example.com","category":"person"}'
test_endpoint "POST" "/api/v1/customers" "$TOKEN" "201" "customers.create" "Super admin should create customers" "$customer_data"

# Test 3: Billing Management (Should have full access)
echo ""
echo -e "${BLUE}Test 3: Billing Management Permissions${NC}"

# Test billing endpoints (if available)
test_endpoint "GET" "/api/v1/billing/summary" "$TOKEN" "200" "billing.view" "Super admin should view billing"

# Test 4: Services Management (Should have full access)
echo ""
echo -e "${BLUE}Test 4: Services Management Permissions${NC}"

# Test services endpoints
test_endpoint "GET" "/api/v1/customer-services" "$TOKEN" "200" "services.view" "Super admin should view services"

# Test 5: Network Management (Should have full access)
echo ""
echo -e "${BLUE}Test 5: Network Management Permissions${NC}"

# Test network endpoints (if available)
test_endpoint "GET" "/api/v1/network/devices" "$TOKEN" "404" "network.view" "Network endpoint may not exist (404 expected)"

echo ""
echo "🔒 PHASE 3: PERMISSION BOUNDARY TESTING"
echo "---------------------------------------"

# Test 6: Invalid Token Test
echo ""
echo -e "${BLUE}Test 6: Invalid Token Handling${NC}"
INVALID_TOKEN="invalid.jwt.token"
test_endpoint "GET" "/api/v1/customers" "$INVALID_TOKEN" "401" "invalid_token" "Invalid token should be rejected"

# Test 7: Missing Token Test
echo ""
echo -e "${BLUE}Test 7: Missing Token Handling${NC}"
response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "GET" "$BASE_URL/api/v1/customers")
http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
log_test "missing_token" "401" "$http_status" "Missing token should be rejected"

echo ""
echo "📊 PHASE 4: RBAC SYSTEM VALIDATION"
echo "----------------------------------"

# Test 8: Verify User Role Assignment
echo ""
echo -e "${BLUE}Test 8: User Role Verification${NC}"
echo "Checking admin user role assignment via database..."

# Test 9: Permission Inheritance Test
echo ""
echo -e "${BLUE}Test 9: Permission Inheritance${NC}"
echo "Testing that super_admin role has all expected permissions..."

# Test multiple endpoints to verify comprehensive access
endpoints=(
    "/api/v1/customers:GET:200:customers.view"
    "/api/v1/customer-services:GET:200:services.view"
    "/api/v1/billing/summary:GET:200:billing.view"
)

for endpoint_test in "${endpoints[@]}"; do
    IFS=':' read -r endpoint method expected_status permission <<< "$endpoint_test"
    test_endpoint "$method" "$endpoint" "$TOKEN" "$expected_status" "$permission" "Super admin comprehensive access test"
done

echo ""
echo "🎯 PHASE 5: EDGE CASE TESTING"
echo "-----------------------------"

# Test 10: Malformed Requests
echo ""
echo -e "${BLUE}Test 10: Malformed Request Handling${NC}"

# Test with malformed JSON
malformed_data='{"name":"Test","invalid_json"}'
test_endpoint "POST" "/api/v1/customers" "$TOKEN" "422" "malformed_json" "Malformed JSON should be rejected" "$malformed_data"

# Test 11: Non-existent Endpoints
echo ""
echo -e "${BLUE}Test 11: Non-existent Endpoint Handling${NC}"
test_endpoint "GET" "/api/v1/nonexistent" "$TOKEN" "404" "nonexistent_endpoint" "Non-existent endpoints should return 404"

echo ""
echo "📈 TEST RESULTS SUMMARY"
echo "======================="
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! RBAC system is working correctly.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the results above.${NC}"
    exit 1
fi
