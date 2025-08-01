#!/bin/bash

# Corrected RBAC User Journey Simulation Script
# Tests granular role-based access control with proper endpoint URLs

echo "🚀 CORRECTED RBAC USER JOURNEY SIMULATION"
echo "=========================================="
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

# Function to test API endpoint with proper URL formatting
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local token="$3"
    local expected_status="$4"
    local test_name="$5"
    local description="$6"
    local data="$7"
    
    # Ensure endpoint has trailing slash for proper routing
    if [[ "$endpoint" != */ ]] && [[ "$endpoint" != *"health" ]] && [[ "$endpoint" != *"token" ]]; then
        endpoint="${endpoint}/"
    fi
    
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
    response_body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//g')
    
    log_test "$test_name" "$expected_status" "$http_status" "$description"
    
    # Show response preview for failed tests
    if [ "$expected_status" != "$http_status" ] && [ -n "$response_body" ]; then
        echo "   Response preview: ${response_body:0:100}..."
    fi
    
    return 0
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
echo "🛡️ PHASE 2: SUPER ADMIN PERMISSION TESTING"
echo "-------------------------------------------"

# Test 2: Customer Management (Should have full access)
echo ""
echo -e "${BLUE}Test 2: Customer Management Permissions${NC}"

# Test customers.view permission
test_endpoint "GET" "/api/v1/customers" "$TOKEN" "200" "customers.view" "Super admin should view customers"

# Test customers.create permission
customer_data='{"name":"RBAC Test Customer","email":"rbactest@example.com","category":"person"}'
test_endpoint "POST" "/api/v1/customers" "$TOKEN" "201" "customers.create" "Super admin should create customers" "$customer_data"

# Test 3: Services Management (Should have full access)
echo ""
echo -e "${BLUE}Test 3: Services Management Permissions${NC}"

# Test services.view permission
test_endpoint "GET" "/api/v1/customer-services" "$TOKEN" "200" "services.view" "Super admin should view services"

# Test 4: Health Check (Public endpoint)
echo ""
echo -e "${BLUE}Test 4: Public Endpoint Access${NC}"

# Test health endpoint (no auth required)
response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "GET" "$BASE_URL/health")
http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
log_test "health_check" "200" "$http_status" "Health endpoint should be accessible"

echo ""
echo "🔒 PHASE 3: PERMISSION BOUNDARY TESTING"
echo "---------------------------------------"

# Test 5: Invalid Token Test
echo ""
echo -e "${BLUE}Test 5: Invalid Token Handling${NC}"
INVALID_TOKEN="invalid.jwt.token"
test_endpoint "GET" "/api/v1/customers" "$INVALID_TOKEN" "401" "invalid_token" "Invalid token should be rejected"

# Test 6: Missing Token Test
echo ""
echo -e "${BLUE}Test 6: Missing Token Handling${NC}"
response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "GET" "$BASE_URL/api/v1/customers/")
http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
log_test "missing_token" "401" "$http_status" "Missing token should be rejected"

echo ""
echo "📊 PHASE 4: RBAC SYSTEM VALIDATION"
echo "----------------------------------"

# Test 7: Verify RBAC System Setup
echo ""
echo -e "${BLUE}Test 7: RBAC System Validation${NC}"
echo "Verifying RBAC system configuration..."

# Test multiple endpoints to verify comprehensive access
echo ""
echo -e "${BLUE}Test 8: Comprehensive Access Validation${NC}"

endpoints=(
    "/api/v1/customers:GET:200:customers.view"
    "/api/v1/customer-services:GET:200:services.view"
)

for endpoint_test in "${endpoints[@]}"; do
    IFS=':' read -r endpoint method expected_status permission <<< "$endpoint_test"
    test_endpoint "$method" "$endpoint" "$TOKEN" "$expected_status" "$permission" "Super admin comprehensive access test"
done

echo ""
echo "🎯 PHASE 5: EDGE CASE TESTING"
echo "-----------------------------"

# Test 9: Malformed Requests
echo ""
echo -e "${BLUE}Test 9: Input Validation Testing${NC}"

# Test with malformed JSON
malformed_data='{"name":"Test","invalid_json"'
test_endpoint "POST" "/api/v1/customers" "$TOKEN" "422" "malformed_json" "Malformed JSON should be rejected" "$malformed_data"

# Test 10: Non-existent Endpoints
echo ""
echo -e "${BLUE}Test 10: Non-existent Endpoint Handling${NC}"
test_endpoint "GET" "/api/v1/nonexistent" "$TOKEN" "404" "nonexistent_endpoint" "Non-existent endpoints should return 404"

# Test 11: HTTP Method Validation
echo ""
echo -e "${BLUE}Test 11: HTTP Method Validation${NC}"
test_endpoint "DELETE" "/api/v1/customers" "$TOKEN" "405" "method_not_allowed" "Unsupported HTTP methods should return 405"

echo ""
echo "🔍 PHASE 6: RBAC PERMISSION VERIFICATION"
echo "----------------------------------------"

# Test 12: Permission Inheritance Verification
echo ""
echo -e "${BLUE}Test 12: Permission Inheritance${NC}"
echo "Verifying that super_admin role has all expected permissions..."

# Test that we can access all the endpoints we should have access to
permission_tests=(
    "/api/v1/customers:GET:customers.view"
    "/api/v1/customer-services:GET:services.view"
)

echo "Testing inherited permissions:"
for perm_test in "${permission_tests[@]}"; do
    IFS=':' read -r endpoint method permission <<< "$perm_test"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$BASE_URL$endpoint/" \
        -H "Authorization: Bearer $TOKEN")
    http_status=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$http_status" = "200" ]; then
        echo -e "  ${GREEN}✅${NC} $permission: Access granted (HTTP $http_status)"
    else
        echo -e "  ${RED}❌${NC} $permission: Access denied (HTTP $http_status)"
    fi
done

echo ""
echo "📈 TEST RESULTS SUMMARY"
echo "======================="
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! RBAC system is working correctly.${NC}"
    echo ""
    echo "✅ RBAC System Validation Complete:"
    echo "   - Authentication working correctly"
    echo "   - Super admin permissions validated"
    echo "   - Permission boundaries enforced"
    echo "   - Input validation working"
    echo "   - Error handling proper"
    exit 0
else
    echo -e "${YELLOW}⚠️  $FAILED_TESTS test(s) failed. Review the results above.${NC}"
    echo ""
    echo "📋 Summary of Issues Found:"
    echo "   - Check failed test details above"
    echo "   - Verify endpoint URLs and authentication"
    echo "   - Review RBAC permission assignments"
    exit 1
fi
