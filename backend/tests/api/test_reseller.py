#!/usr/bin/env python3
"""
Comprehensive Reseller System Test Script

Tests the complete reseller authentication and management system implementation.
"""
import requests
import json
import sys
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000/api/v1"

class ResellerSystemTester:
    """Test class for reseller system validation"""
    
    def __init__(self):
        self.admin_token: Optional[str] = None
        self.reseller_token: Optional[str] = None
        self.test_reseller_id: Optional[int] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    token: str = None, expect_success: bool = True) -> Dict[str, Any]:
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            result = response.json() if response.content else {}
            
            if expect_success and response.status_code >= 400:
                self.log(f"Request failed: {method} {endpoint} - {response.status_code}: {result}", "ERROR")
                return {"error": True, "status_code": response.status_code, "detail": result}
            
            return {"error": False, "status_code": response.status_code, "data": result}
            
        except Exception as e:
            self.log(f"Request exception: {method} {endpoint} - {str(e)}", "ERROR")
            return {"error": True, "exception": str(e)}
    
    def test_admin_authentication(self) -> bool:
        """Test admin authentication to get token for reseller management"""
        self.log("Testing admin authentication...")
        
        # Use form data for OAuth2 token endpoint
        url = f"{BASE_URL}/auth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = "username=admin&password=admin123"
        
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json() if response.content else {}
            
            if response.status_code == 200 and result.get("access_token"):
                self.admin_token = result["access_token"]
                self.log("✅ Admin authentication successful")
                self.log(f"   Token type: {result.get('token_type')}")
                return True
            else:
                self.log(f"❌ Admin authentication failed: {response.status_code} - {result}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Admin authentication exception: {str(e)}", "ERROR")
            return False
    
    def test_reseller_creation(self) -> bool:
        """Test reseller creation via admin endpoints"""
        if not self.admin_token:
            self.log("❌ No admin token available for reseller creation", "ERROR")
            return False
        
        self.log("Testing reseller creation...")
        
        reseller_data = {
            "name": "Test Reseller Company",
            "email": "testreseller@example.com",
            "code": "TEST001",
            "contact_person": "John Doe",
            "phone": "+1234567890",
            "address": "123 Test Street",
            "city": "Test City",
            "commission_percentage": 15.0,
            "territory": "North Region",
            "customer_limit": 100
        }
        
        result = self.make_request("POST", "/resellers/", reseller_data, self.admin_token, expect_success=False)
        
        if result.get("error"):
            self.log(f"❌ Reseller creation failed: {result.get('detail', 'Unknown error')}", "ERROR")
            return False
        
        reseller = result.get("data", {})
        self.test_reseller_id = reseller.get("id")
        
        if self.test_reseller_id:
            self.log(f"✅ Reseller created successfully with ID: {self.test_reseller_id}")
            return True
        else:
            self.log("❌ Reseller creation returned no ID", "ERROR")
            return False
    
    def test_reseller_password_setup(self) -> bool:
        """Test setting password for reseller"""
        if not self.admin_token or not self.test_reseller_id:
            self.log("❌ No admin token or reseller ID for password setup", "ERROR")
            return False
        
        self.log("Testing reseller password setup...")
        
        password_data = {
            "reseller_id": self.test_reseller_id,
            "password": "testpass123"
        }
        
        result = self.make_request("POST", "/reseller-auth/set-password", password_data, self.admin_token, expect_success=False)
        
        if result.get("error"):
            self.log(f"❌ Password setup failed: {result.get('detail', 'Unknown error')}", "ERROR")
            return False
        
        self.log("✅ Reseller password set successfully")
        return True
    
    def test_reseller_authentication(self) -> bool:
        """Test reseller login and token generation"""
        self.log("Testing reseller authentication...")
        
        login_data = {
            "email": "testreseller@example.com",
            "password": "testpass123"
        }
        
        result = self.make_request("POST", "/reseller-auth/login", login_data, expect_success=False)
        
        if result.get("error"):
            self.log(f"❌ Reseller authentication failed: {result.get('detail', 'Unknown error')}", "ERROR")
            return False
        
        auth_response = result.get("data", {})
        self.reseller_token = auth_response.get("access_token")
        
        if self.reseller_token:
            self.log("✅ Reseller authentication successful")
            self.log(f"   Token type: {auth_response.get('token_type')}")
            self.log(f"   Expires in: {auth_response.get('expires_in')} seconds")
            return True
        else:
            self.log("❌ Reseller authentication returned no token", "ERROR")
            return False
    
    def test_reseller_profile_access(self) -> bool:
        """Test reseller profile and permissions access"""
        if not self.reseller_token:
            self.log("❌ No reseller token for profile access", "ERROR")
            return False
        
        self.log("Testing reseller profile access...")
        
        # Test /me endpoint
        result = self.make_request("GET", "/reseller-auth/me", token=self.reseller_token, expect_success=False)
        
        if result.get("error"):
            self.log(f"❌ Reseller profile access failed: {result.get('detail', 'Unknown error')}", "ERROR")
            return False
        
        profile = result.get("data", {})
        reseller_info = profile.get("reseller", {})
        permissions = profile.get("permissions", {})
        
        self.log("✅ Reseller profile access successful")
        self.log(f"   Name: {reseller_info.get('name')}")
        self.log(f"   Email: {reseller_info.get('email')}")
        self.log(f"   Territory: {reseller_info.get('territory')}")
        self.log(f"   Commission: {reseller_info.get('commission_percentage')}%")
        self.log(f"   Customer Limit: {permissions.get('customer_limit')}")
        
        return True
    
    def test_reseller_management_endpoints(self) -> bool:
        """Test reseller management endpoints"""
        if not self.admin_token or not self.test_reseller_id:
            self.log("❌ No admin token or reseller ID for management testing", "ERROR")
            return False
        
        self.log("Testing reseller management endpoints...")
        
        # Test list resellers
        result = self.make_request("GET", "/resellers/", token=self.admin_token, expect_success=False)
        if result.get("error"):
            self.log(f"❌ List resellers failed: {result.get('detail')}", "ERROR")
            return False
        
        resellers = result.get("data", {}).get("items", [])
        self.log(f"✅ List resellers successful - Found {len(resellers)} resellers")
        
        # Test get reseller details
        result = self.make_request("GET", f"/resellers/{self.test_reseller_id}", token=self.admin_token, expect_success=False)
        if result.get("error"):
            self.log(f"❌ Get reseller details failed: {result.get('detail')}", "ERROR")
            return False
        
        reseller = result.get("data", {})
        self.log(f"✅ Get reseller details successful - {reseller.get('name')}")
        
        # Test reseller stats
        result = self.make_request("GET", f"/resellers/{self.test_reseller_id}/stats", token=self.admin_token, expect_success=False)
        if result.get("error"):
            self.log(f"❌ Get reseller stats failed: {result.get('detail')}", "ERROR")
            return False
        
        stats = result.get("data", {})
        self.log(f"✅ Get reseller stats successful - {stats.get('customer_count', 0)} customers")
        
        return True
    
    def test_token_refresh(self) -> bool:
        """Test token refresh functionality"""
        if not self.reseller_token:
            self.log("❌ No reseller token for refresh testing", "ERROR")
            return False
        
        self.log("Testing token refresh...")
        
        result = self.make_request("POST", "/reseller-auth/refresh", token=self.reseller_token, expect_success=False)
        
        if result.get("error"):
            self.log(f"❌ Token refresh failed: {result.get('detail', 'Unknown error')}", "ERROR")
            return False
        
        refresh_response = result.get("data", {})
        new_token = refresh_response.get("access_token")
        
        if new_token:
            self.log("✅ Token refresh successful")
            self.reseller_token = new_token  # Update token
            return True
        else:
            self.log("❌ Token refresh returned no new token", "ERROR")
            return False
    
    def run_comprehensive_test(self) -> bool:
        """Run complete reseller system test suite"""
        self.log("🚀 Starting Comprehensive Reseller System Test")
        self.log("=" * 60)
        
        tests = [
            ("Admin Authentication", self.test_admin_authentication),
            ("Reseller Creation", self.test_reseller_creation),
            ("Reseller Password Setup", self.test_reseller_password_setup),
            ("Reseller Authentication", self.test_reseller_authentication),
            ("Reseller Profile Access", self.test_reseller_profile_access),
            ("Reseller Management Endpoints", self.test_reseller_management_endpoints),
            ("Token Refresh", self.test_token_refresh),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    self.log(f"❌ {test_name} FAILED", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name} FAILED with exception: {str(e)}", "ERROR")
        
        self.log("\n" + "=" * 60)
        self.log(f"🎯 TEST RESULTS: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - Reseller system is fully functional!", "SUCCESS")
            return True
        else:
            self.log(f"⚠️  {total - passed} tests failed - System needs attention", "WARNING")
            return False

def main():
    """Main test execution"""
    tester = ResellerSystemTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
