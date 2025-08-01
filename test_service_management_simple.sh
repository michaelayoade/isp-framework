#!/bin/bash

# Simple Service Management Test Script
# Tests basic service management endpoints without complex data creation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

echo "🚀 SIMPLE SERVICE MANAGEMENT TESTING"
echo "===================================="

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local token=$3
    local expected_status=$4
    local test_name=$5
    local description=$6
    local data=$7
    
    echo ""
    echo -e "${BLUE}Testing: $test_name${NC}"
    echo "Description: $description"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $token")
    fi
    
    http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//g')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} | $test_name | Expected: $expected_status, Got: $http_code"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} | $test_name | Expected: $expected_status, Got: $http_code"
        echo "   Response preview: ${body:0:100}..."
        ((FAILED++))
    fi
}

# Get authentication token
echo "🔐 AUTHENTICATION"
echo "----------------"

auth_response=$(curl -s -X POST "$BASE_URL/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123")

TOKEN=$(echo "$auth_response" | jq -r '.access_token')
if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ Authentication successful${NC}"
else
    echo -e "${RED}❌ Authentication failed${NC}"
    exit 1
fi

echo ""
echo "📊 SERVICE MANAGEMENT ENDPOINT TESTING"
echo "======================================"

# Test service listing endpoints (should work)
test_endpoint "GET" "/api/v1/services/internet/" "$TOKEN" "200" "internet_list" "List internet services"
test_endpoint "GET" "/api/v1/services/voice/" "$TOKEN" "200" "voice_list" "List voice services"  
test_endpoint "GET" "/api/v1/services/bundle/" "$TOKEN" "200" "bundle_list" "List bundle services"

# Test service search endpoint
test_endpoint "GET" "/api/v1/services/search" "$TOKEN" "200" "service_search" "Search all services"

# Test service overview endpoint
test_endpoint "GET" "/api/v1/services/overview" "$TOKEN" "200" "service_overview" "Get service overview"

# Test individual service endpoints (should return 404 for non-existent services)
test_endpoint "GET" "/api/v1/services/internet/999" "$TOKEN" "404" "internet_get_missing" "Get non-existent internet service"
test_endpoint "GET" "/api/v1/services/voice/999" "$TOKEN" "404" "voice_get_missing" "Get non-existent voice service"
test_endpoint "GET" "/api/v1/services/bundle/999" "$TOKEN" "404" "bundle_get_missing" "Get non-existent bundle service"

echo ""
echo "📈 TEST RESULTS SUMMARY"
echo "======================"
echo "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All service management endpoint tests passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️ Some tests failed. Service management endpoints need attention.${NC}"
    exit 1
fi
