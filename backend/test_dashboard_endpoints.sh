#!/bin/bash

# Dashboard API Endpoints Test Script
# Tests all dashboard endpoints with curl

set -e

# Configuration
BASE_URL="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dashboard API Endpoints Test ===${NC}"
echo "Base URL: $BASE_URL"
echo

# Function to print test results
print_result() {
    local test_name="$1"
    local status_code="$2"
    local expected="$3"
    
    if [ "$status_code" = "$expected" ]; then
        echo -e "${GREEN}✓ $test_name (HTTP $status_code)${NC}"
    else
        echo -e "${RED}✗ $test_name (HTTP $status_code, expected $expected)${NC}"
    fi
}

# Function to extract JSON field
extract_json() {
    echo "$1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('$2', 'N/A'))"
}

echo -e "${YELLOW}Step 1: Admin Authentication${NC}"
echo "Authenticating as admin user..."

AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "'"$ADMIN_USERNAME"'", "password": "'"$ADMIN_PASSWORD"'"}')

STATUS_CODE="${AUTH_RESPONSE: -3}"
RESPONSE_BODY="${AUTH_RESPONSE%???}"

print_result "Admin Authentication" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))")
    echo "Access token obtained: ${ACCESS_TOKEN:0:20}..."
    echo
else
    echo -e "${RED}Authentication failed. Cannot proceed with dashboard tests.${NC}"
    echo "Response: $RESPONSE_BODY"
    exit 1
fi

# Set authorization header
AUTH_HEADER="Authorization: Bearer $ACCESS_TOKEN"

echo -e "${YELLOW}Step 2: Dashboard KPIs Endpoint${NC}"

# Test 1: Get all KPIs (default period)
echo "Testing GET /dashboard/kpis (all KPIs, default period)..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/kpis" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get All KPIs" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Sample response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool | head -20
    echo "..."
fi
echo

# Test 2: Get financial KPIs only
echo "Testing GET /dashboard/kpis?categories=financial..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/kpis?categories=financial" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Financial KPIs" "$STATUS_CODE" "200"
echo

# Test 3: Get specific metrics
echo "Testing GET /dashboard/kpis?metrics=total_revenue,arpu..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/kpis?metrics=total_revenue,arpu" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Specific Metrics" "$STATUS_CODE" "200"
echo

# Test 4: Get KPIs with custom period
echo "Testing GET /dashboard/kpis?period=week..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/kpis?period=week" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Weekly KPIs" "$STATUS_CODE" "200"
echo

echo -e "${YELLOW}Step 3: Single Metric Endpoint${NC}"

# Test 5: Get single metric
echo "Testing GET /dashboard/metrics/total_revenue..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/metrics/total_revenue" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Single Metric" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Metric response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo

# Test 6: Get non-existent metric
echo "Testing GET /dashboard/metrics/non_existent_metric..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/metrics/non_existent_metric" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Non-existent Metric" "$STATUS_CODE" "404"
echo

echo -e "${YELLOW}Step 4: Financial Report Endpoint${NC}"

# Test 7: Get financial report
echo "Testing GET /dashboard/reports/financial..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/reports/financial" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Financial Report" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Financial report summary:"
    echo "$RESPONSE_BODY" | python3 -m json.tool | head -30
    echo "..."
fi
echo

# Test 8: Get financial report with breakdown
echo "Testing GET /dashboard/reports/financial?breakdown_by=plan..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/reports/financial?breakdown_by=plan" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Financial Report with Breakdown" "$STATUS_CODE" "200"
echo

echo -e "${YELLOW}Step 5: Network Report Endpoint${NC}"

# Test 9: Get network report
echo "Testing GET /dashboard/reports/network..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/reports/network" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Network Report" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Network report summary:"
    echo "$RESPONSE_BODY" | python3 -m json.tool | head -20
    echo "..."
fi
echo

echo -e "${YELLOW}Step 6: Customer Report Endpoint${NC}"

# Test 10: Get customer report
echo "Testing GET /dashboard/reports/customer..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/reports/customer" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Customer Report" "$STATUS_CODE" "200"
echo

echo -e "${YELLOW}Step 7: Operational Report Endpoint${NC}"

# Test 11: Get operational report
echo "Testing GET /dashboard/reports/operational..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/reports/operational" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Operational Report" "$STATUS_CODE" "200"
echo

echo -e "${YELLOW}Step 8: Dashboard Widgets Endpoint${NC}"

# Test 12: Get dashboard widgets
echo "Testing GET /dashboard/widgets..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/widgets" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Dashboard Widgets" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Widgets response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool | head -30
    echo "..."
fi
echo

# Test 13: Get widgets by category
echo "Testing GET /dashboard/widgets?categories=financial..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/widgets?categories=financial" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Financial Widgets" "$STATUS_CODE" "200"
echo

echo -e "${YELLOW}Step 9: Available Metrics Endpoint${NC}"

# Test 14: Get available metrics
echo "Testing GET /dashboard/metrics..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/metrics" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Available Metrics" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Available metrics:"
    echo "$RESPONSE_BODY" | python3 -m json.tool | head -40
    echo "..."
fi
echo

echo -e "${YELLOW}Step 10: Available Segments Endpoint${NC}"

# Test 15: Get available segments
echo "Testing GET /dashboard/segments..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/segments" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Available Segments" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Available segments:"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo

echo -e "${YELLOW}Step 11: Cache Management Endpoints${NC}"

# Test 16: Get cache stats (admin only)
echo "Testing GET /dashboard/cache/stats..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/cache/stats" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Get Cache Stats" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Cache stats:"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo

# Test 17: Clear cache (admin only)
echo "Testing POST /dashboard/cache/clear..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X POST "$BASE_URL/dashboard/cache/clear" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Clear Cache" "$STATUS_CODE" "200"

if [ "$STATUS_CODE" = "200" ]; then
    echo "Cache clear response:"
    echo "$RESPONSE_BODY" | python3 -m json.tool
fi
echo

echo -e "${YELLOW}Step 12: Error Handling Tests${NC}"

# Test 18: Test without authentication
echo "Testing GET /dashboard/kpis without authentication..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/kpis")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Unauthenticated Request" "$STATUS_CODE" "401"
echo

# Test 19: Test with invalid period
echo "Testing GET /dashboard/kpis?period=invalid..."
RESPONSE=$(curl -s -w "%{http_code}" \
    -X GET "$BASE_URL/dashboard/kpis?period=invalid" \
    -H "$AUTH_HEADER")

STATUS_CODE="${RESPONSE: -3}"
RESPONSE_BODY="${RESPONSE%???}"
print_result "Invalid Period Parameter" "$STATUS_CODE" "422"
echo

echo -e "${BLUE}=== Dashboard API Test Summary ===${NC}"
echo "All dashboard endpoint tests completed!"
echo
echo "Key endpoints tested:"
echo "- GET /dashboard/kpis (with various filters)"
echo "- GET /dashboard/metrics/{metric_key}"
echo "- GET /dashboard/reports/financial"
echo "- GET /dashboard/reports/network"
echo "- GET /dashboard/reports/customer"
echo "- GET /dashboard/reports/operational"
echo "- GET /dashboard/widgets"
echo "- GET /dashboard/metrics (list available)"
echo "- GET /dashboard/segments"
echo "- GET /dashboard/cache/stats"
echo "- POST /dashboard/cache/clear"
echo
echo -e "${GREEN}Dashboard API testing completed!${NC}"
