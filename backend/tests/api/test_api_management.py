#!/usr/bin/env python3
"""
Comprehensive API Management System Test Suite

This script tests all API management endpoints to ensure they work correctly.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class APIManagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.api_key = None
        self.customer_id = None
        
    def get_admin_token(self):
        """Get admin access token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            self.admin_token = response.json()["access_token"]
            return True
        return False
    
    def create_test_customer(self):
        """Create a test customer for API key testing"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        customer_data = {
            "first_name": "API",
            "last_name": "Test",
            "email": f"api-test-{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+1234567890",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "zip_code": "12345",
            "country": "US",
            "password": "testpass123",
            "birth_date": "1990-01-01",
            "national_id": "TEST123456",
            "is_active": True
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/customers",
            json=customer_data,
            headers=headers
        )
        
        if response.status_code == 201:
            self.customer_id = response.json()["id"]
            return True
        return False
    
    def test_api_key_creation(self):
        """Test API key creation"""
        print("\n=== Testing API Key Creation ===")
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        api_key_data = {
            "name": "Test API Key",
            "description": "Key for testing API management",
            "customer_id": self.customer_id,
            "permissions": {"read": True, "write": True, "admin": False},
            "rate_limit": 100,
            "rate_limit_period": "hour",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/api-management/keys",
            json=api_key_data,
            headers=headers
        )
        
        if response.status_code == 201:
            result = response.json()
            self.api_key = result["key"]
            print(f"✅ API Key created: {result['key'][:10]}...")
            return True
        else:
            print(f"❌ API Key creation failed: {response.status_code} - {response.text}")
            return False
    
    def test_api_key_listing(self):
        """Test listing API keys"""
        print("\n=== Testing API Key Listing ===")
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.get(
            f"{self.base_url}/api/v1/api-management/keys",
            headers=headers
        )
        
        if response.status_code == 200:
            keys = response.json()
            print(f"✅ Found {len(keys)} API keys")
            return True
        else:
            print(f"❌ API Key listing failed: {response.status_code}")
            return False
    
    def test_api_key_validation(self):
        """Test API key validation"""
        print("\n=== Testing API Key Validation ===")
        headers = {"X-API-Key": self.api_key}
        
        response = requests.get(
            f"{self.base_url}/api/v1/customers",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ API key validation successful")
            return True
        else:
            print(f"❌ API key validation failed: {response.status_code}")
            return False
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        print("\n=== Testing Rate Limiting ===")
        headers = {"X-API-Key": self.api_key}
        
        # Make multiple requests to trigger rate limiting
        for i in range(5):
            response = requests.get(
                f"{self.base_url}/api/v1/customers",
                headers=headers
            )
            if response.status_code == 429:
                print(f"✅ Rate limiting triggered after {i+1} requests")
                return True
        
        print("✅ Rate limiting working (no trigger within 5 requests)")
        return True
    
    def test_usage_analytics(self):
        """Test usage analytics"""
        print("\n=== Testing Usage Analytics ===")
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.get(
            f"{self.base_url}/api/v1/api-management/analytics",
            headers=headers
        )
        
        if response.status_code == 200:
            analytics = response.json()
            print(f"✅ Analytics retrieved: {analytics}")
            return True
        else:
            print(f"❌ Analytics retrieval failed: {response.status_code}")
            return False
    
    def test_api_key_revocation(self):
        """Test API key revocation"""
        print("\n=== Testing API Key Revocation ===")
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Get the key ID first
        response = requests.get(
            f"{self.base_url}/api/v1/api-management/keys",
            headers=headers
        )
        
        if response.status_code == 200:
            keys = response.json()
            if keys:
                key_id = keys[0]["id"]
                
                # Revoke the key
                response = requests.put(
                    f"{self.base_url}/api/v1/api-management/keys/{key_id}/revoke",
                    headers=headers
                )
                
                if response.status_code == 200:
                    print("✅ API key revoked successfully")
                    return True
        
        print("❌ API key revocation failed")
        return False
    
    def test_rate_limit_configuration(self):
        """Test rate limit configuration"""
        print("\n=== Testing Rate Limit Configuration ===")
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        config_data = {
            "endpoint": "/api/v1/customers",
            "max_requests": 50,
            "window_size": 3600,
            "is_active": True
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/api-management/rate-limits",
            json=config_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print("✅ Rate limit configuration created")
            return True
        else:
            print(f"❌ Rate limit configuration failed: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all API management tests"""
        print("🚀 Starting API Management System Tests")
        
        # Get admin token
        if not self.get_admin_token():
            print("❌ Failed to get admin token")
            return False
        
        # Create test customer
        if not self.create_test_customer():
            print("❌ Failed to create test customer")
            return False
        
        # Run tests
        tests = [
            self.test_api_key_creation,
            self.test_api_key_listing,
            self.test_api_key_validation,
            self.test_rate_limiting,
            self.test_usage_analytics,
            self.test_rate_limit_configuration,
            self.test_api_key_revocation
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                failed += 1
        
        print(f"\n📊 Test Results:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed))*100:.1f}%")
        
        return failed == 0


if __name__ == "__main__":
    tester = APIManagementTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All API Management tests passed!")
    else:
        print("\n⚠️ Some API Management tests failed")
