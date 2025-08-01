#!/bin/bash

# ISP Framework Service Management User Journey Testing
# Tests comprehensive service management workflows with curl

echo "🚀 SERVICE MANAGEMENT USER JOURNEY TESTING"
echo "==========================================="
echo ""

# Configuration
BASE_URL="https://marketing.dotmac.ng"
AUTH_ENDPOINT="$BASE_URL/api/v1/auth/token"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Service IDs for cleanup
INTERNET_SERVICE_ID=""
VOICE_SERVICE_ID=""
BUNDLE_SERVICE_ID=""
PROVISIONING_ID=""
TEMPLATE_ID=""

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

# Function to test API endpoint with proper error handling
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local token="$3"
    local expected_status="$4"
    local test_name="$5"
    local description="$6"
    local data="$7"
    
    # Ensure endpoint has trailing slash for proper routing
    if [[ "$endpoint" != */ ]] && [[ "$endpoint" != *"health" ]] && [[ "$endpoint" != *"token" ]] && [[ "$endpoint" != *"overview" ]]; then
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
    
    # Extract service IDs for later use
    if [ "$expected_status" = "$http_status" ] && [ "$http_status" = "201" ]; then
        service_id=$(echo "$response_body" | jq -r '.id // empty')
        if [ -n "$service_id" ] && [ "$service_id" != "null" ]; then
            case "$test_name" in
                "internet_service_create") INTERNET_SERVICE_ID="$service_id" ;;
                "voice_service_create") VOICE_SERVICE_ID="$service_id" ;;
                "bundle_service_create") BUNDLE_SERVICE_ID="$service_id" ;;
                "provisioning_create") PROVISIONING_ID="$service_id" ;;
                "template_create") TEMPLATE_ID="$service_id" ;;
            esac
            echo "   Created resource ID: $service_id"
        fi
    fi
    
    # Show response preview for failed tests or important data
    if [ "$expected_status" != "$http_status" ] || [ "$http_status" = "201" ]; then
        echo "   Response preview: ${response_body:0:150}..."
    fi
    
    return 0
}

echo "🔐 PHASE 1: AUTHENTICATION"
echo "-------------------------"

auth_response=$(curl -s -X POST "$BASE_URL/api/v1/auth/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123")

if [ $? -eq 0 ]; then
    TOKEN=$(echo "$auth_response" | jq -r '.access_token')
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        echo "✅ Authentication successful"
        echo "Token: ${TOKEN:0:50}..."
    else
        echo "❌ Authentication failed"
        echo "Response: $auth_response"
        exit 1
    fi
else
    echo "❌ Authentication failed"
    exit 1
fi

echo ""
echo "📊 PHASE 2: SERVICE OVERVIEW & STATISTICS"
echo "-----------------------------------------"

# Test services overview
echo ""
echo -e "${BLUE}Test 1: Services Overview${NC}"
test_endpoint "GET" "/api/v1/services/overview" "$TOKEN" "200" "services_overview" "Get comprehensive services overview"

echo ""
echo "🌐 PHASE 3: INTERNET SERVICE MANAGEMENT"
echo "======================================="

# Test internet service creation
echo ""
echo -e "${BLUE}Test 2: Internet Service Creation${NC}"
internet_service_data='{
    "name": "Test Internet Service",
    "description": "High-speed internet service for testing",
    "download_speed": 100,
    "upload_speed": 50,
    "data_limit": 1000,
    "monthly_price": 49.99,
    "setup_fee": 0,
    "cancellation_fee": 0,
    "is_active": true,
    "is_public": true,
    "priority": 1,
    "activation_method": "manual"
}'

test_endpoint "POST" "/api/v1/services/internet" "$TOKEN" "201" "internet_service_create" "Create new internet service" "$internet_service_data"

# Test internet service listing
echo ""
echo -e "${BLUE}Test 3: Internet Service Listing${NC}"
test_endpoint "GET" "/api/v1/services/internet" "$TOKEN" "200" "internet_service_list" "List all internet services"

# Test internet service retrieval
if [ -n "$INTERNET_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Test 4: Internet Service Retrieval${NC}"
    test_endpoint "GET" "/api/v1/services/internet/$INTERNET_SERVICE_ID" "$TOKEN" "200" "internet_service_get" "Get specific internet service"
    
    # Test internet service update
    echo ""
    echo -e "${BLUE}Test 5: Internet Service Update${NC}"
    internet_update_data='{
        "name": "Updated Internet Service",
        "price": 59.99,
        "download_speed": 150
    }'
    test_endpoint "PUT" "/api/v1/services/internet/$INTERNET_SERVICE_ID" "$TOKEN" "200" "internet_service_update" "Update internet service" "$internet_update_data"
fi

echo ""
echo "📞 PHASE 4: VOICE SERVICE MANAGEMENT"
echo "===================================="

# Test voice service creation
echo ""
echo -e "${BLUE}Test 6: Voice Service Creation${NC}"
voice_service_data='{
    "name": "Test Voice Service",
    "description": "VoIP service for testing",
    "included_minutes": 500,
    "per_minute_rate": 0.05,
    "monthly_price": 29.99,
    "setup_fee": 0,
    "cancellation_fee": 0,
    "is_active": true,
    "is_public": true,
    "codec": "G.711",
    "quality": "premium",
    "priority": 1
}'

test_endpoint "POST" "/api/v1/services/voice" "$TOKEN" "201" "voice_service_create" "Create new voice service" "$voice_service_data"

# Test voice service listing
echo ""
echo -e "${BLUE}Test 7: Voice Service Listing${NC}"
test_endpoint "GET" "/api/v1/services/voice" "$TOKEN" "200" "voice_service_list" "List all voice services"

# Test voice service retrieval
if [ -n "$VOICE_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Test 8: Voice Service Retrieval${NC}"
    test_endpoint "GET" "/api/v1/services/voice/$VOICE_SERVICE_ID" "$TOKEN" "200" "voice_service_get" "Get specific voice service"
fi

echo ""
echo "📦 PHASE 5: BUNDLE SERVICE MANAGEMENT"
echo "====================================="

# Test bundle service creation
echo ""
echo -e "${BLUE}Test 9: Bundle Service Creation${NC}"
bundle_service_data='{
    "name": "Test Bundle Service",
    "description": "Internet + Voice bundle for testing",
    "bundle_price": 69.99,
    "individual_price": 79.98,
    "discount_amount": 9.99,
    "discount_percentage": 12.5,
    "is_active": true,
    "is_public": true,
    "priority": 1,
    "minimum_term_months": 12,
    "early_termination_fee": 50.00
}'

test_endpoint "POST" "/api/v1/services/bundle" "$TOKEN" "201" "bundle_service_create" "Create new bundle service" "$bundle_service_data"

# Test bundle service listing
echo ""
echo -e "${BLUE}Test 10: Bundle Service Listing${NC}"
test_endpoint "GET" "/api/v1/services/bundle" "$TOKEN" "200" "bundle_service_list" "List all bundle services"

# Test bundle service retrieval
if [ -n "$BUNDLE_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Test 11: Bundle Service Retrieval${NC}"
    test_endpoint "GET" "/api/v1/services/bundle/$BUNDLE_SERVICE_ID" "$TOKEN" "200" "bundle_service_get" "Get specific bundle service"
fi

echo ""
echo "🔍 PHASE 6: SERVICE SEARCH & FILTERING"
echo "======================================"

# Test service search
echo ""
echo -e "${BLUE}Test 12: Service Search${NC}"
test_endpoint "GET" "/api/v1/services/search?search_term=Test&service_type=internet" "$TOKEN" "200" "service_search" "Search services with filters"

# Test service search by price range
echo ""
echo -e "${BLUE}Test 13: Service Search by Price${NC}"
test_endpoint "GET" "/api/v1/services/search?min_price=20&max_price=100" "$TOKEN" "200" "service_search_price" "Search services by price range"

echo ""
echo "⚙️ PHASE 7: SERVICE PROVISIONING MANAGEMENT"
echo "==========================================="

# Test provisioning template creation
echo ""
echo -e "${BLUE}Test 14: Provisioning Template Creation${NC}"
template_data='{
    "name": "Test Internet Provisioning Template",
    "description": "Automated internet service provisioning",
    "service_type": "internet",
    "automation_level": 3,
    "requires_approval": false,
    "estimated_duration": 30,
    "steps": [
        {
            "step_name": "validate_customer",
            "step_order": 1,
            "automation_level": 5,
            "estimated_duration": 5
        },
        {
            "step_name": "configure_service",
            "step_order": 2,
            "automation_level": 4,
            "estimated_duration": 15
        },
        {
            "step_name": "activate_service",
            "step_order": 3,
            "automation_level": 3,
            "estimated_duration": 10
        }
    ]
}'

test_endpoint "POST" "/api/v1/service-provisioning/templates" "$TOKEN" "201" "template_create" "Create provisioning template" "$template_data"

# Test provisioning template listing
echo ""
echo -e "${BLUE}Test 15: Provisioning Template Listing${NC}"
test_endpoint "GET" "/api/v1/service-provisioning/templates" "$TOKEN" "200" "template_list" "List provisioning templates"

# Create service provisioning workflow
if [ -n "$INTERNET_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Test 16: Service Provisioning Creation${NC}"
    provisioning_data='{
        "service_id": '$INTERNET_SERVICE_ID',
        "service_type": "internet",
        "customer_id": 3,
        "priority": 5,
        "scheduled_date": "2025-08-02T10:00:00Z",
        "configuration": {
            "auto_activate": true,
            "send_notifications": true
        }
    }'
    
    test_endpoint "POST" "/api/v1/service-provisioning" "$TOKEN" "201" "provisioning_create" "Create service provisioning workflow" "$provisioning_data"
fi

# Test provisioning queue
echo ""
echo -e "${BLUE}Test 17: Provisioning Queue${NC}"
test_endpoint "GET" "/api/v1/service-provisioning/queue" "$TOKEN" "200" "provisioning_queue" "Get provisioning queue"

# Test provisioning statistics
echo ""
echo -e "${BLUE}Test 18: Provisioning Statistics${NC}"
test_endpoint "GET" "/api/v1/service-provisioning/statistics" "$TOKEN" "200" "provisioning_stats" "Get provisioning statistics"

echo ""
echo "🔧 PHASE 8: PROVISIONING WORKFLOW CONTROL"
echo "========================================="

if [ -n "$PROVISIONING_ID" ]; then
    # Test workflow start
    echo ""
    echo -e "${BLUE}Test 19: Start Provisioning Workflow${NC}"
    test_endpoint "POST" "/api/v1/service-provisioning/$PROVISIONING_ID/start" "$TOKEN" "200" "provisioning_start" "Start provisioning workflow"
    
    # Test workflow status check
    echo ""
    echo -e "${BLUE}Test 20: Check Provisioning Status${NC}"
    test_endpoint "GET" "/api/v1/service-provisioning/$PROVISIONING_ID" "$TOKEN" "200" "provisioning_status" "Check provisioning workflow status"
    
    # Test workflow pause
    echo ""
    echo -e "${BLUE}Test 21: Pause Provisioning Workflow${NC}"
    test_endpoint "POST" "/api/v1/service-provisioning/$PROVISIONING_ID/pause?reason=Testing" "$TOKEN" "200" "provisioning_pause" "Pause provisioning workflow"
    
    # Test workflow resume
    echo ""
    echo -e "${BLUE}Test 22: Resume Provisioning Workflow${NC}"
    test_endpoint "POST" "/api/v1/service-provisioning/$PROVISIONING_ID/resume" "$TOKEN" "200" "provisioning_resume" "Resume provisioning workflow"
fi

echo ""
echo "🏥 PHASE 9: SYSTEM HEALTH & MONITORING"
echo "======================================"

# Test provisioning system health
echo ""
echo -e "${BLUE}Test 23: Provisioning System Health${NC}"
test_endpoint "GET" "/api/v1/service-provisioning/health" "$TOKEN" "200" "provisioning_health" "Check provisioning system health"

echo ""
echo "🧹 PHASE 10: CLEANUP OPERATIONS"
echo "==============================="

# Clean up created resources
if [ -n "$PROVISIONING_ID" ]; then
    echo ""
    echo -e "${BLUE}Cleanup 1: Cancel Provisioning Workflow${NC}"
    test_endpoint "POST" "/api/v1/service-provisioning/$PROVISIONING_ID/cancel?reason=Test cleanup" "$TOKEN" "200" "provisioning_cancel" "Cancel provisioning workflow for cleanup"
fi

if [ -n "$BUNDLE_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Cleanup 2: Delete Bundle Service${NC}"
    test_endpoint "DELETE" "/api/v1/services/bundle/$BUNDLE_SERVICE_ID" "$TOKEN" "204" "bundle_service_delete" "Delete bundle service"
fi

if [ -n "$VOICE_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Cleanup 3: Delete Voice Service${NC}"
    test_endpoint "DELETE" "/api/v1/services/voice/$VOICE_SERVICE_ID" "$TOKEN" "204" "voice_service_delete" "Delete voice service"
fi

if [ -n "$INTERNET_SERVICE_ID" ]; then
    echo ""
    echo -e "${BLUE}Cleanup 4: Delete Internet Service${NC}"
    test_endpoint "DELETE" "/api/v1/services/internet/$INTERNET_SERVICE_ID" "$TOKEN" "204" "internet_service_delete" "Delete internet service"
fi

echo ""
echo "📈 TEST RESULTS SUMMARY"
echo "======================="
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL SERVICE MANAGEMENT TESTS PASSED!${NC}"
    echo ""
    echo "✅ Service Management System Validation Complete:"
    echo "   - Internet service lifecycle management working"
    echo "   - Voice service lifecycle management working"
    echo "   - Bundle service lifecycle management working"
    echo "   - Service search and filtering working"
    echo "   - Provisioning workflow management working"
    echo "   - Template management working"
    echo "   - System health monitoring working"
    exit 0
else
    echo -e "${YELLOW}⚠️  $FAILED_TESTS test(s) failed. Review the results above.${NC}"
    echo ""
    echo "📋 Service Management Test Summary:"
    echo "   - Check failed test details above"
    echo "   - Verify service creation and management"
    echo "   - Review provisioning workflow operations"
    exit 1
fi
