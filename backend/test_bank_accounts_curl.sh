#!/bin/bash

# Bank Account API Test Script
# Comprehensive curl-based testing for bank account endpoints

set -e

# Configuration
BASE_URL="http://localhost:8000/api/v1"
ADMIN_EMAIL="admin@ispframework.com"
ADMIN_PASSWORD="admin123"
TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

run_test() {
    local test_name="$1"
    local expected_status="$2"
    shift 2
    
    ((TOTAL_TESTS++))
    log_info "Running test: $test_name"
    
    # Run curl command and capture response
    local response=$(curl -s -w "\n%{http_code}" "$@")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [[ "$http_code" == "$expected_status" ]]; then
        log_success "$test_name (HTTP $http_code)"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        log_error "$test_name (Expected HTTP $expected_status, got $http_code)"
        echo "$body"
    fi
    
    echo "----------------------------------------"
}

# Authentication
authenticate() {
    log_info "Authenticating as admin..."
    
    local auth_response=$(curl -s -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}")
    
    TOKEN=$(echo "$auth_response" | jq -r '.access_token // empty')
    
    if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
        log_error "Authentication failed"
        echo "Response: $auth_response"
        exit 1
    fi
    
    log_success "Authentication successful"
    echo "Token: ${TOKEN:0:20}..."
    echo "----------------------------------------"
}

# Test functions
test_create_platform_account() {
    run_test "Create Platform Collection Account" 201 \
        -X POST "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "owner_type": "PLATFORM",
            "bank_name": "First Bank",
            "account_number": "1234567890",
            "account_name": "ISP Framework Collections",
            "bank_code": "011",
            "currency": "NGN",
            "country": "NG",
            "alias": "Primary Collection Account",
            "description": "Main platform collection account"
        }'
}

test_create_reseller_account() {
    run_test "Create Reseller Payout Account" 201 \
        -X POST "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "owner_type": "RESELLER",
            "owner_id": 1,
            "bank_name": "GTBank",
            "account_number": "0987654321",
            "account_name": "Reseller Payouts Ltd",
            "bank_code": "058",
            "currency": "NGN",
            "country": "NG",
            "alias": "Reseller Main Account"
        }'
}

test_create_duplicate_account() {
    run_test "Create Duplicate Account (Should Fail)" 422 \
        -X POST "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "owner_type": "PLATFORM",
            "bank_name": "First Bank",
            "account_number": "1234567890",
            "account_name": "Duplicate Account",
            "bank_code": "011"
        }'
}

test_create_invalid_reseller_account() {
    run_test "Create Reseller Account Without owner_id (Should Fail)" 422 \
        -X POST "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "owner_type": "RESELLER",
            "bank_name": "UBA",
            "account_number": "1111111111",
            "account_name": "Invalid Reseller Account"
        }'
}

test_list_all_accounts() {
    run_test "List All Bank Accounts" 200 \
        -X GET "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN"
}

test_list_platform_accounts() {
    run_test "List Platform Accounts Only" 200 \
        -X GET "$BASE_URL/bank-accounts/?owner_type=PLATFORM" \
        -H "Authorization: Bearer $TOKEN"
}

test_list_active_accounts() {
    run_test "List Active Accounts Only" 200 \
        -X GET "$BASE_URL/bank-accounts/?active_only=true" \
        -H "Authorization: Bearer $TOKEN"
}

test_get_account_by_id() {
    # First, get the list to find an account ID
    local accounts_response=$(curl -s -X GET "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN")
    
    local account_id=$(echo "$accounts_response" | jq -r '.accounts[0].id // empty')
    
    if [[ -n "$account_id" && "$account_id" != "null" ]]; then
        run_test "Get Bank Account by ID" 200 \
            -X GET "$BASE_URL/bank-accounts/$account_id" \
            -H "Authorization: Bearer $TOKEN"
    else
        log_warning "No accounts found to test get by ID"
    fi
}

test_update_account() {
    # Get an account ID first
    local accounts_response=$(curl -s -X GET "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN")
    
    local account_id=$(echo "$accounts_response" | jq -r '.accounts[0].id // empty')
    
    if [[ -n "$account_id" && "$account_id" != "null" ]]; then
        run_test "Update Bank Account" 200 \
            -X PUT "$BASE_URL/bank-accounts/$account_id" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
                "alias": "Updated Account Alias",
                "description": "Updated account description"
            }'
    else
        log_warning "No accounts found to test update"
    fi
}

test_verify_account() {
    # Get an account ID first
    local accounts_response=$(curl -s -X GET "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN")
    
    local account_id=$(echo "$accounts_response" | jq -r '.accounts[0].id // empty')
    
    if [[ -n "$account_id" && "$account_id" != "null" ]]; then
        run_test "Verify Bank Account" 200 \
            -X POST "$BASE_URL/bank-accounts/$account_id/verify" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d '{
                "verification_notes": "Account verified via manual process"
            }'
    else
        log_warning "No accounts found to test verification"
    fi
}

test_get_platform_collection_accounts() {
    run_test "Get Platform Collection Accounts" 200 \
        -X GET "$BASE_URL/bank-accounts/platform/collection-accounts" \
        -H "Authorization: Bearer $TOKEN"
}

test_get_reseller_payout_accounts() {
    run_test "Get Reseller Payout Accounts" 200 \
        -X GET "$BASE_URL/bank-accounts/reseller/1/payout-accounts" \
        -H "Authorization: Bearer $TOKEN"
}

test_get_statistics() {
    run_test "Get Bank Account Statistics" 200 \
        -X GET "$BASE_URL/bank-accounts/statistics" \
        -H "Authorization: Bearer $TOKEN"
}

test_get_nonexistent_account() {
    run_test "Get Non-existent Account (Should Fail)" 404 \
        -X GET "$BASE_URL/bank-accounts/99999" \
        -H "Authorization: Bearer $TOKEN"
}

test_unauthorized_access() {
    run_test "Unauthorized Access (Should Fail)" 401 \
        -X GET "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer invalid_token"
}

test_delete_account() {
    # Get an account ID first
    local accounts_response=$(curl -s -X GET "$BASE_URL/bank-accounts/" \
        -H "Authorization: Bearer $TOKEN")
    
    local account_id=$(echo "$accounts_response" | jq -r '.accounts[-1].id // empty')
    
    if [[ -n "$account_id" && "$account_id" != "null" ]]; then
        run_test "Delete Bank Account (Soft Delete)" 200 \
            -X DELETE "$BASE_URL/bank-accounts/$account_id" \
            -H "Authorization: Bearer $TOKEN"
    else
        log_warning "No accounts found to test deletion"
    fi
}

# Main test execution
main() {
    echo "========================================"
    echo "Bank Account API Test Suite"
    echo "========================================"
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. JSON responses will not be formatted."
    fi
    
    # Authenticate
    authenticate
    
    # Run tests
    log_info "Starting bank account API tests..."
    echo ""
    
    # CRUD Tests
    test_create_platform_account
    test_create_reseller_account
    test_create_duplicate_account
    test_create_invalid_reseller_account
    
    # Read Tests
    test_list_all_accounts
    test_list_platform_accounts
    test_list_active_accounts
    test_get_account_by_id
    
    # Update Tests
    test_update_account
    test_verify_account
    
    # Specialized Endpoint Tests
    test_get_platform_collection_accounts
    test_get_reseller_payout_accounts
    test_get_statistics
    
    # Error Handling Tests
    test_get_nonexistent_account
    test_unauthorized_access
    
    # Cleanup Tests
    test_delete_account
    
    # Test Summary
    echo ""
    echo "========================================"
    echo "Test Summary"
    echo "========================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
