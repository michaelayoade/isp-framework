"""Basic smoke tests for Device Management API.

These tests exercise key endpoints using the shared TestClient fixture.
They are intentionally lightweight to give us coverage while the full
feature-level tests are authored later.
"""

import pytest


@pytest.mark.order(1)
def test_device_dashboard_summary(client):
    """Dashboard summary should return 200 and include expected keys."""
    resp = client.get("/api/v1/devices/dashboard/summary")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for key in ("total_devices", "online_devices", "active_alerts"):
        assert key in data


@pytest.mark.order(2)
def test_device_list(client):
    """Device list (paginated) should return 200 even when empty."""
    resp = client.get("/api/v1/devices/")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list) or "items" in body  # supports pagination wrappers


"""
Comprehensive Device Management System Test Script

This script tests all device management workflows including:
- Authentication and authorization
- Device registration and management
- SNMP monitoring and health checks
- Configuration backup and restore
- Alert management
- Dashboard and analytics
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class DeviceManagementTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {"Content-Type": "application/json"}
        
    def authenticate(self) -> bool:
        """Authenticate with the API and get access token"""
        print("🔐 Testing Authentication...")
        
        # Try different authentication endpoints
        auth_endpoints = [
            "/auth/login",
            "/auth/admin/login", 
            "/oauth/token"
        ]
        
        for endpoint in auth_endpoints:
            try:
                # Try form data for OAuth
                if "oauth" in endpoint:
                    data = {
                        "grant_type": "password",
                        "username": ADMIN_USERNAME,
                        "password": ADMIN_PASSWORD,
                        "client_id": "isp-framework-client"
                    }
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        data=data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                else:
                    # Try JSON data for regular auth
                    data = {
                        "username": ADMIN_USERNAME,
                        "password": ADMIN_PASSWORD
                    }
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        headers=self.headers
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    if "access_token" in result:
                        self.auth_token = result["access_token"]
                        self.headers["Authorization"] = f"Bearer {self.auth_token}"
                        print(f"✅ Authentication successful via {endpoint}")
                        return True
                    elif "token" in result:
                        self.auth_token = result["token"]
                        self.headers["Authorization"] = f"Bearer {self.auth_token}"
                        print(f"✅ Authentication successful via {endpoint}")
                        return True
                        
            except Exception as e:
                print(f"❌ Auth endpoint {endpoint} failed: {e}")
                continue
        
        print("❌ Authentication failed - proceeding without auth for testing")
        return False
    
    def test_dashboard(self) -> bool:
        """Test device management dashboard"""
        print("\n📊 Testing Device Management Dashboard...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/devices/dashboard/summary",
                headers=self.headers
            )
            
            if response.status_code == 200:
                dashboard_data = response.json()
                print("✅ Dashboard endpoint accessible")
                print(f"   Total devices: {dashboard_data.get('total_devices', 0)}")
                print(f"   Online devices: {dashboard_data.get('online_devices', 0)}")
                print(f"   Active alerts: {dashboard_data.get('active_alerts', 0)}")
                return True
            else:
                print(f"❌ Dashboard failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard test failed: {e}")
            return False
    
    def test_device_listing(self) -> bool:
        """Test device listing endpoint"""
        print("\n📋 Testing Device Listing...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/devices/devices",
                headers=self.headers
            )
            
            if response.status_code == 200:
                devices = response.json()
                print(f"✅ Device listing successful - Found {len(devices)} devices")
                return True
            else:
                print(f"❌ Device listing failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Device listing test failed: {e}")
            return False
    
    def test_device_registration(self) -> Optional[int]:
        """Test device registration"""
        print("\n➕ Testing Device Registration...")
        
        test_device = {
            "hostname": "test-router-01",
            "device_type": "router",
            "vendor": "MikroTik",
            "model": "RB4011iGS+",
            "ip_address": "192.168.1.1",
            "snmp_community": "public",
            "snmp_version": "v2c",
            "location": "Main Office",
            "description": "Test router for device management testing"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/devices/devices",
                json=test_device,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                device_data = response.json()
                device_id = device_data.get("id")
                print(f"✅ Device registration successful - Device ID: {device_id}")
                return device_id
            else:
                print(f"❌ Device registration failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Device registration test failed: {e}")
            return None
    
    def test_device_health_check(self, device_id: int) -> bool:
        """Test device health check"""
        print(f"\n🏥 Testing Device Health Check (ID: {device_id})...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/devices/devices/{device_id}/health-check",
                headers=self.headers
            )
            
            if response.status_code == 200:
                health_data = response.json()
                print("✅ Health check successful")
                print(f"   Overall status: {health_data.get('overall_status', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Health check test failed: {e}")
            return False
    
    def test_config_backup(self, device_id: int) -> bool:
        """Test configuration backup"""
        print(f"\n💾 Testing Configuration Backup (ID: {device_id})...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/devices/devices/{device_id}/backup",
                json={"backup_type": "full"},
                headers=self.headers
            )
            
            if response.status_code in [200, 202]:
                backup_data = response.json()
                print("✅ Configuration backup initiated")
                print(f"   Backup ID: {backup_data.get('backup_id', 'unknown')}")
                return True
            else:
                print(f"❌ Config backup failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Config backup test failed: {e}")
            return False
    
    def test_device_metrics(self, device_id: int) -> bool:
        """Test device metrics collection"""
        print(f"\n📈 Testing Device Metrics Collection (ID: {device_id})...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/devices/devices/{device_id}/collect-metrics",
                headers=self.headers
            )
            
            if response.status_code in [200, 202]:
                print("✅ Metrics collection initiated")
                return True
            else:
                print(f"❌ Metrics collection failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Metrics collection test failed: {e}")
            return False
    
    def test_alert_management(self) -> bool:
        """Test alert management"""
        print("\n🚨 Testing Alert Management...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/devices/alerts",
                headers=self.headers
            )
            
            if response.status_code == 200:
                alerts = response.json()
                print(f"✅ Alert listing successful - Found {len(alerts)} alerts")
                return True
            else:
                print(f"❌ Alert listing failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Alert management test failed: {e}")
            return False
    
    def test_device_discovery(self) -> bool:
        """Test device discovery"""
        print("\n🔍 Testing Device Discovery...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/devices/discovery/subnet",
                json={
                    "subnet": "192.168.1.0/24",
                    "snmp_community": "public"
                },
                headers=self.headers
            )
            
            if response.status_code in [200, 202]:
                print("✅ Device discovery initiated")
                return True
            else:
                print(f"❌ Device discovery failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Device discovery test failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all device management tests"""
        print("🚀 Starting Comprehensive Device Management System Test")
        print("=" * 60)
        
        # Test authentication
        auth_success = self.authenticate()
        
        # Test core functionality
        tests_passed = 0
        total_tests = 0
        
        # Test dashboard
        total_tests += 1
        if self.test_dashboard():
            tests_passed += 1
        
        # Test device listing
        total_tests += 1
        if self.test_device_listing():
            tests_passed += 1
        
        # Test device registration
        total_tests += 1
        device_id = self.test_device_registration()
        if device_id:
            tests_passed += 1
            
            # Test device-specific operations if registration succeeded
            if device_id:
                total_tests += 1
                if self.test_device_health_check(device_id):
                    tests_passed += 1
                
                total_tests += 1
                if self.test_config_backup(device_id):
                    tests_passed += 1
                
                total_tests += 1
                if self.test_device_metrics(device_id):
                    tests_passed += 1
        
        # Test alert management
        total_tests += 1
        if self.test_alert_management():
            tests_passed += 1
        
        # Test device discovery
        total_tests += 1
        if self.test_device_discovery():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests passed: {tests_passed}/{total_tests}")
        print(f"Success rate: {(tests_passed/total_tests)*100:.1f}%")
        
        if auth_success:
            print("✅ Authentication: Working")
        else:
            print("❌ Authentication: Failed")
        
        if tests_passed == total_tests:
            print("🎉 All device management tests PASSED!")
            return True
        else:
            print("⚠️  Some device management tests FAILED")
            return False


if __name__ == "__main__":
    tester = DeviceManagementTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
