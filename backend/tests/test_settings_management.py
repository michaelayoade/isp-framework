#!/usr/bin/env python3
"""
Settings Management Integration Test

Tests the complete settings management system including:
- Settings models and database operations
- Feature flags functionality
- Secrets manager integration
- API endpoints and authentication
- Runtime configuration management
"""
import pytest
import requests
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_CREDENTIALS = {
    "username": "admin@example.com",
    "password": "admin123"
}

class SettingsManagementTester:
    """Comprehensive settings management test suite."""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
    
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self) -> bool:
        """Authenticate with the API."""
        try:
            # Try to get admin token
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                data=ADMIN_CREDENTIALS
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Error: {str(e)}")
            return False
    
    def test_settings_endpoints(self) -> bool:
        """Test settings management endpoints."""
        try:
            # Test get all settings
            response = self.session.get(f"{BASE_URL}/settings/")
            if response.status_code != 200:
                self.log_result("Get All Settings", False, f"Status: {response.status_code}")
                return False
            
            settings_list = response.json()
            self.log_result("Get All Settings", True, f"Retrieved {len(settings_list)} settings")
            
            # Test create setting
            test_setting = {
                "key": "test.setting.example",
                "value": "test_value",
                "setting_type": "string",
                "category": "general",
                "description": "Test setting for validation",
                "is_secret": False,
                "is_readonly": False,
                "requires_restart": False
            }
            
            response = self.session.post(f"{BASE_URL}/settings/", json=test_setting)
            if response.status_code == 200:
                self.log_result("Create Setting", True, "Test setting created")
                
                # Test get specific setting
                response = self.session.get(f"{BASE_URL}/settings/test.setting.example")
                if response.status_code == 200:
                    setting_data = response.json()
                    if setting_data["value"] == "test_value":
                        self.log_result("Get Specific Setting", True, "Retrieved correct value")
                    else:
                        self.log_result("Get Specific Setting", False, "Incorrect value returned")
                else:
                    self.log_result("Get Specific Setting", False, f"Status: {response.status_code}")
                
                # Test update setting
                update_data = {
                    "value": "updated_test_value",
                    "change_reason": "Integration test update"
                }
                response = self.session.put(f"{BASE_URL}/settings/test.setting.example", json=update_data)
                if response.status_code == 200:
                    self.log_result("Update Setting", True, "Setting updated successfully")
                else:
                    self.log_result("Update Setting", False, f"Status: {response.status_code}")
                
                # Test setting history
                response = self.session.get(f"{BASE_URL}/settings/test.setting.example/history")
                if response.status_code == 200:
                    history = response.json()
                    self.log_result("Setting History", True, f"Retrieved {len(history)} history entries")
                else:
                    self.log_result("Setting History", False, f"Status: {response.status_code}")
                
                # Clean up - delete test setting
                response = self.session.delete(f"{BASE_URL}/settings/test.setting.example")
                if response.status_code == 200:
                    self.log_result("Delete Setting", True, "Test setting deleted")
                else:
                    self.log_result("Delete Setting", False, f"Status: {response.status_code}")
            else:
                self.log_result("Create Setting", False, f"Status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Settings Endpoints", False, f"Error: {str(e)}")
            return False
    
    def test_feature_flags(self) -> bool:
        """Test feature flags functionality."""
        try:
            # Test get all feature flags
            response = self.session.get(f"{BASE_URL}/settings/flags/")
            if response.status_code == 200:
                flags = response.json()
                self.log_result("Get Feature Flags", True, f"Retrieved {len(flags)} flags")
            else:
                self.log_result("Get Feature Flags", False, f"Status: {response.status_code}")
                return False
            
            # Test check specific feature flag
            response = self.session.get(f"{BASE_URL}/settings/flags/test_feature")
            if response.status_code in [200, 404]:  # 404 is OK if flag doesn't exist
                self.log_result("Check Feature Flag", True, "Feature flag check working")
            else:
                self.log_result("Check Feature Flag", False, f"Status: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_result("Feature Flags", False, f"Error: {str(e)}")
            return False
    
    def test_settings_categories_and_types(self) -> bool:
        """Test settings metadata endpoints."""
        try:
            # Test get categories
            response = self.session.get(f"{BASE_URL}/settings/categories/")
            if response.status_code == 200:
                categories = response.json()
                self.log_result("Get Categories", True, f"Retrieved {len(categories)} categories")
            else:
                self.log_result("Get Categories", False, f"Status: {response.status_code}")
                return False
            
            # Test get types
            response = self.session.get(f"{BASE_URL}/settings/types/")
            if response.status_code == 200:
                types = response.json()
                self.log_result("Get Types", True, f"Retrieved {len(types)} types")
            else:
                self.log_result("Get Types", False, f"Status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Settings Metadata", False, f"Error: {str(e)}")
            return False
    
    def test_settings_initialization(self) -> bool:
        """Test settings initialization."""
        try:
            response = self.session.post(f"{BASE_URL}/settings/initialize")
            if response.status_code == 200:
                result = response.json()
                self.log_result("Settings Initialization", True, f"Created {result.get('created_count', 0)} default settings")
            else:
                self.log_result("Settings Initialization", False, f"Status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Settings Initialization", False, f"Error: {str(e)}")
            return False
    
    def test_secrets_manager(self) -> bool:
        """Test secrets manager functionality."""
        try:
            # Test environment backend
            from app.core.secrets_manager import SecretsManager, get_secret, set_secret
            
            # Create test secrets manager
            secrets = SecretsManager()
            
            # Test setting and getting secrets
            test_key = "test.secret.key"
            test_value = "test_secret_value_123"
            
            if set_secret(test_key, test_value):
                retrieved_value = get_secret(test_key)
                if retrieved_value == test_value:
                    self.log_result("Secrets Manager", True, "Secret storage and retrieval working")
                else:
                    self.log_result("Secrets Manager", False, "Retrieved value doesn't match")
                    return False
            else:
                self.log_result("Secrets Manager", False, "Failed to set secret")
                return False
            
            # Test health check
            health = secrets.health_check()
            if health["status"] in ["healthy", "unknown"]:
                self.log_result("Secrets Health Check", True, f"Status: {health['status']}")
            else:
                self.log_result("Secrets Health Check", False, f"Status: {health['status']}")
            
            return True
            
        except Exception as e:
            self.log_result("Secrets Manager", False, f"Error: {str(e)}")
            return False
    
    def test_runtime_configuration(self) -> bool:
        """Test runtime configuration integration."""
        try:
            from app.core.config import get_runtime_setting, initialize_settings_integration
            
            # Test settings integration
            initialize_settings_integration()
            self.log_result("Settings Integration", True, "Settings integration initialized")
            
            # Test runtime setting retrieval
            test_value = get_runtime_setting("app.name", "ISP Framework")
            if test_value:
                self.log_result("Runtime Settings", True, f"Retrieved setting: {test_value}")
            else:
                self.log_result("Runtime Settings", False, "Failed to retrieve runtime setting")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Runtime Configuration", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all settings management tests."""
        print("🚀 Starting Settings Management Integration Tests")
        print("=" * 60)
        
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code != 200:
                print(f"❌ Server not accessible at {BASE_URL}")
                return {"success": False, "error": "Server not running"}
        except Exception as e:
            print(f"❌ Cannot connect to server: {str(e)}")
            return {"success": False, "error": f"Connection failed: {str(e)}"}
        
        # Run tests
        tests = [
            ("Authentication", self.authenticate),
            ("Settings Endpoints", self.test_settings_endpoints),
            ("Feature Flags", self.test_feature_flags),
            ("Settings Metadata", self.test_settings_categories_and_types),
            ("Settings Initialization", self.test_settings_initialization),
            ("Secrets Manager", self.test_secrets_manager),
            ("Runtime Configuration", self.test_runtime_configuration),
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} tests...")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   {result['details']}")
        
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print("\n🎉 All settings management tests passed!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        
        return {
            "success": overall_success,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "results": self.test_results
        }


def main():
    """Main test execution."""
    tester = SettingsManagementTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("settings_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: settings_test_results.json")
    
    # Exit with appropriate code
    exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
