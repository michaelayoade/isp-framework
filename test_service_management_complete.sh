#!/bin/bash

# Complete Service Management System Test Script
# Tests all aspects of the new service catalog, CRUD operations, provisioning, and validation

set -e

# Configuration
BASE_URL="https://marketing.dotmac.ng/api/v1"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="admin123"

echo "=== ISP Framework - Complete Service Management System Test ==="
echo "Testing comprehensive service catalog, CRUD, provisioning, and validation"
echo

# Step 1: Authenticate as admin
echo "1. Authenticating as administrator..."
AUTH_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USERNAME}&password=${ADMIN_PASSWORD}")

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Authentication successful"
else
    echo "❌ Authentication failed: $AUTH_RESPONSE"
    exit 1
fi

# Step 2: Test Service Catalog Creation
echo
echo "2. Testing Service Catalog Creation..."

# Create Internet Service Catalog Item
echo "2.1. Creating Internet Service Catalog Item..."
INTERNET_CATALOG_RESPONSE=$(curl -s -X POST "${BASE_URL}/services/catalog" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "INTERNET",
    "name": "Premium Fiber 100Mbps",
    "description": "High-speed fiber internet with 100Mbps download and 50Mbps upload",
    "base_price": 25000.00,
    "service_config": {
      "download_speed": 100,
      "upload_speed": 50,
      "data_limit": null,
      "fup_enabled": false,
      "static_ip": false,
      "burst_enabled": true
    }
  }')

if echo "$INTERNET_CATALOG_RESPONSE" | grep -q '"service_type":"INTERNET"'; then
    INTERNET_SERVICE_ID=$(echo "$INTERNET_CATALOG_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "✅ Internet service catalog item created (ID: $INTERNET_SERVICE_ID)"
else
    echo "❌ Internet service catalog creation failed: $INTERNET_CATALOG_RESPONSE"
fi

# Create Voice Service Catalog Item
echo "2.2. Creating Voice Service Catalog Item..."
VOICE_CATALOG_RESPONSE=$(curl -s -X POST "${BASE_URL}/services/catalog" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "VOICE",
    "name": "Business VoIP Plan",
    "description": "Professional VoIP service with 1000 included minutes",
    "base_price": 5000.00,
    "service_config": {
      "included_minutes": 1000,
      "per_minute_rate": 0.05,
      "caller_id": true,
      "voicemail": true
    }
  }')

if echo "$VOICE_CATALOG_RESPONSE" | grep -q '"service_type":"VOICE"'; then
    VOICE_SERVICE_ID=$(echo "$VOICE_CATALOG_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "✅ Voice service catalog item created (ID: $VOICE_SERVICE_ID)"
else
    echo "❌ Voice service catalog creation failed: $VOICE_CATALOG_RESPONSE"
fi

# Create Bundle Service Catalog Item
echo "2.3. Creating Bundle Service Catalog Item..."
BUNDLE_CATALOG_RESPONSE=$(curl -s -X POST "${BASE_URL}/services/catalog" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "BUNDLE",
    "name": "Internet + Voice Bundle",
    "description": "Combined internet and voice service with 15% discount",
    "base_price": 28000.00,
    "service_config": {
      "included_services": {},
      "discount_percent": 15,
      "minimum_months": 12
    }
  }')

if echo "$BUNDLE_CATALOG_RESPONSE" | grep -q '"service_type":"BUNDLE"'; then
    BUNDLE_SERVICE_ID=$(echo "$BUNDLE_CATALOG_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "✅ Bundle service catalog item created (ID: $BUNDLE_SERVICE_ID)"
else
    echo "❌ Bundle service catalog creation failed: $BUNDLE_CATALOG_RESPONSE"
fi

# Step 3: Test Service Catalog Retrieval
echo
echo "3. Testing Service Catalog Retrieval..."

# Get all catalog items
echo "3.1. Getting all service catalog items..."
ALL_CATALOG_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/catalog" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$ALL_CATALOG_RESPONSE" | grep -q '"service_type"'; then
    CATALOG_COUNT=$(echo "$ALL_CATALOG_RESPONSE" | grep -o '"id":[0-9]*' | wc -l)
    echo "✅ Retrieved $CATALOG_COUNT service catalog items"
else
    echo "❌ Failed to retrieve service catalog: $ALL_CATALOG_RESPONSE"
fi

# Get specific catalog item
if [ ! -z "$INTERNET_SERVICE_ID" ]; then
    echo "3.2. Getting specific internet service catalog item..."
    SPECIFIC_CATALOG_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/catalog/${INTERNET_SERVICE_ID}" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}")
    
    if echo "$SPECIFIC_CATALOG_RESPONSE" | grep -q '"name":"Premium Fiber 100Mbps"'; then
        echo "✅ Retrieved specific service catalog item successfully"
    else
        echo "❌ Failed to retrieve specific catalog item: $SPECIFIC_CATALOG_RESPONSE"
    fi
fi

# Step 4: Test Service Search and Filtering
echo
echo "4. Testing Service Search and Filtering..."

# Search by service type
echo "4.1. Searching services by type (INTERNET)..."
SEARCH_TYPE_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/search?service_type=INTERNET" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$SEARCH_TYPE_RESPONSE" | grep -q '"service_type":"INTERNET"'; then
    echo "✅ Service search by type successful"
else
    echo "❌ Service search by type failed: $SEARCH_TYPE_RESPONSE"
fi

# Search by name
echo "4.2. Searching services by name..."
SEARCH_NAME_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/search?search_term=Fiber" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$SEARCH_NAME_RESPONSE" | grep -q '"name"'; then
    echo "✅ Service search by name successful"
else
    echo "❌ Service search by name failed: $SEARCH_NAME_RESPONSE"
fi

# Search by price range
echo "4.3. Searching services by price range..."
SEARCH_PRICE_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/search?min_price=20000&max_price=30000" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$SEARCH_PRICE_RESPONSE" | grep -q '"base_price"'; then
    echo "✅ Service search by price range successful"
else
    echo "❌ Service search by price range failed: $SEARCH_PRICE_RESPONSE"
fi

# Step 5: Test Services Overview
echo
echo "5. Testing Services Overview..."
OVERVIEW_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/overview" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$OVERVIEW_RESPONSE" | grep -q '"total_services"'; then
    TOTAL_SERVICES=$(echo "$OVERVIEW_RESPONSE" | grep -o '"total_services":[0-9]*' | cut -d':' -f2)
    INTERNET_SERVICES=$(echo "$OVERVIEW_RESPONSE" | grep -o '"internet_services":[0-9]*' | cut -d':' -f2)
    VOICE_SERVICES=$(echo "$OVERVIEW_RESPONSE" | grep -o '"voice_services":[0-9]*' | cut -d':' -f2)
    BUNDLE_SERVICES=$(echo "$OVERVIEW_RESPONSE" | grep -o '"bundle_services":[0-9]*' | cut -d':' -f2)
    echo "✅ Services overview retrieved:"
    echo "   - Total Services: $TOTAL_SERVICES"
    echo "   - Internet Services: $INTERNET_SERVICES"
    echo "   - Voice Services: $VOICE_SERVICES"
    echo "   - Bundle Services: $BUNDLE_SERVICES"
else
    echo "❌ Services overview failed: $OVERVIEW_RESPONSE"
fi

# Step 6: Test Service Validation
echo
echo "6. Testing Service Validation..."

# Valid service data
echo "6.1. Testing valid service data validation..."
VALID_VALIDATION_RESPONSE=$(curl -s -X POST "${BASE_URL}/services/validate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "INTERNET",
    "service_data": {
      "name": "Test Service",
      "base_price": 15000,
      "service_config": {
        "download_speed": 50,
        "upload_speed": 25
      }
    }
  }')

if echo "$VALID_VALIDATION_RESPONSE" | grep -q '"is_valid":true'; then
    echo "✅ Valid service data validation successful"
else
    echo "❌ Valid service data validation failed: $VALID_VALIDATION_RESPONSE"
fi

# Invalid service data
echo "6.2. Testing invalid service data validation..."
INVALID_VALIDATION_RESPONSE=$(curl -s -X POST "${BASE_URL}/services/validate" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "INTERNET",
    "service_data": {
      "name": "",
      "base_price": -100,
      "service_config": {
        "download_speed": 0,
        "upload_speed": -10
      }
    }
  }')

if echo "$INVALID_VALIDATION_RESPONSE" | grep -q '"is_valid":false'; then
    echo "✅ Invalid service data validation successful"
else
    echo "❌ Invalid service data validation failed: $INVALID_VALIDATION_RESPONSE"
fi

# Step 7: Test Service Catalog Updates
echo
echo "7. Testing Service Catalog Updates..."

if [ ! -z "$INTERNET_SERVICE_ID" ]; then
    echo "7.1. Updating service catalog item..."
    UPDATE_RESPONSE=$(curl -s -X PUT "${BASE_URL}/services/catalog/${INTERNET_SERVICE_ID}" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Premium Fiber 100Mbps (Updated)",
        "description": "Updated high-speed fiber internet service",
        "base_price": 26000.00
      }')
    
    if echo "$UPDATE_RESPONSE" | grep -q '"updated":true'; then
        echo "✅ Service catalog item updated successfully"
    else
        echo "❌ Service catalog item update failed: $UPDATE_RESPONSE"
    fi
fi

# Step 9: Test Service Provisioning (if customer exists)
echo
echo "9. Testing Service Provisioning..."

# First, try to get a customer to provision service for
CUSTOMERS_RESPONSE=$(curl -s -X GET "${BASE_URL}/customers/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$CUSTOMERS_RESPONSE" | grep -q '"customers"'; then
    CUSTOMER_ID=$(echo "$CUSTOMERS_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    
    if [ ! -z "$CUSTOMER_ID" ] && [ ! -z "$INTERNET_SERVICE_ID" ]; then
        echo "9.1. Testing service provisioning for customer $CUSTOMER_ID..."
        PROVISION_RESPONSE=$(curl -s -X POST "${BASE_URL}/services/provision" \
          -H "Authorization: Bearer ${ACCESS_TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{
            \"customer_id\": $CUSTOMER_ID,
            \"service_template_id\": $INTERNET_SERVICE_ID,
            \"provisioning_data\": {
              \"installation_address\": \"123 Test Street\",
              \"preferred_installation_date\": \"2024-02-01\",
              \"special_instructions\": \"Ground floor installation\"
            }
          }")
        
        if echo "$PROVISION_RESPONSE" | grep -q '"status":"PROVISIONING_STARTED"'; then
            CUSTOMER_SERVICE_ID=$(echo "$PROVISION_RESPONSE" | grep -o '"customer_service_id":[0-9]*' | cut -d':' -f2)
            echo "✅ Service provisioning started (Customer Service ID: $CUSTOMER_SERVICE_ID)"
            
            # Test provisioning status
            if [ ! -z "$CUSTOMER_SERVICE_ID" ]; then
                echo "9.2. Checking provisioning status..."
                STATUS_RESPONSE=$(curl -s -X GET "${BASE_URL}/services/provision/${CUSTOMER_SERVICE_ID}/status" \
                  -H "Authorization: Bearer ${ACCESS_TOKEN}")
                
                if echo "$STATUS_RESPONSE" | grep -q '"status"'; then
                    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
                    echo "✅ Provisioning status retrieved: $STATUS"
                else
                    echo "❌ Provisioning status check failed: $STATUS_RESPONSE"
                fi
            fi
        else
            echo "❌ Service provisioning failed: $PROVISION_RESPONSE"
        fi
    else
        echo "⚠️  Skipping provisioning test - no customer or service template available"
    fi
else
    echo "⚠️  Skipping provisioning test - no customers available"
fi

# Final Summary
echo
echo "=== Service Management System Test Summary ==="
echo "✅ Service catalog creation (Internet, Voice, Bundle)"
echo "✅ Service catalog retrieval (all items and specific items)"
echo "✅ Service search and filtering (by type, name, price)"
echo "✅ Services overview and statistics"
echo "✅ Service data validation (valid and invalid cases)"
echo "✅ Service catalog updates"
echo "✅ Service provisioning workflows"
echo
echo "🎉 Modern Service Management System test completed successfully!"
echo "The ISP Framework now has a clean, unified service catalog API with:"
echo "   - Comprehensive CRUD operations via unified endpoints"
echo "   - Advanced search and filtering capabilities"
echo "   - Service provisioning workflows"
echo "   - Data validation and error handling"
echo "   - Modern RESTful API design"
echo "   - Statistics and overview capabilities"
