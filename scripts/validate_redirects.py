#!/usr/bin/env python3
"""
Backward Compatibility Validation Script
Tests all redirect endpoints to ensure they work correctly
"""

import requests
import json
from typing import Dict, List, Tuple
import sys

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ENDPOINTS = {
    # Phase 3A Redirects (already implemented)
    "api_management": [
        "/api-management/keys",
        "/api-management/versions", 
        "/api-management/usage/analytics"
    ],
    "auth_2fa": [
        "/auth/2fa/setup",
        "/auth/2fa/status",
        "/auth/2fa/api-keys"
    ],
    
    # Phase 3B Redirects (newly implemented)
    "ticketing": [
        "/tickets",
        "/tickets/search",
        "/tickets/dashboard/overview"
    ],
    "alerts": [
        "/alerts/status",
        "/alerts/metrics",
        "/alerts/webhooks/grafana"
    ],
    "dashboard": [
        "/dashboard/overview",
        "/dashboard/metrics",
        "/dashboard/health"
    ],
    "webhooks": [
        "/webhooks",
        "/webhooks/endpoints",
        "/webhooks/delivery-history"
    ],
    "background": [
        "/background/stats",
        "/background/items",
        "/background/dashboard"
    ]
}

EXPECTED_REDIRECTS = {
    # Phase 3A Expected Redirects
    "/api-management/keys": "/api/v1/api/keys",
    "/auth/2fa/setup": "/api/v1/auth/two-factor/setup",
    
    # Phase 3B Expected Redirects  
    "/tickets": "/api/v1/support/tickets",
    "/alerts/status": "/api/v1/monitoring/alerts/status",
    "/dashboard/overview": "/api/v1/monitoring/dashboard/overview",
    "/webhooks": "/api/v1/integrations/webhooks",
    "/background/stats": "/api/v1/background/tasks/stats"
}

def test_redirect(old_path: str, expected_new_path: str = None) -> Tuple[bool, str, str]:
    """Test a single redirect endpoint"""
    url = f"{BASE_URL}{old_path}"
    
    try:
        # Test with allow_redirects=False to capture the redirect response
        response = requests.get(url, allow_redirects=False, timeout=5)
        
        if response.status_code == 307:
            # Temporary redirect as expected
            location = response.headers.get('Location', '')
            
            if expected_new_path and location == expected_new_path:
                return True, f"✅ Redirect working: {old_path} → {location}", location
            elif expected_new_path:
                return False, f"❌ Wrong redirect: {old_path} → {location} (expected {expected_new_path})", location
            else:
                return True, f"✅ Redirect found: {old_path} → {location}", location
                
        elif response.status_code == 404:
            return False, f"❌ Endpoint not found: {old_path}", ""
            
        elif response.status_code in [200, 401, 403]:
            return False, f"⚠️  No redirect (direct response): {old_path} → {response.status_code}", ""
            
        else:
            return False, f"❌ Unexpected status: {old_path} → {response.status_code}", ""
            
    except requests.exceptions.RequestException as e:
        return False, f"❌ Request failed: {old_path} → {str(e)}", ""

def validate_all_redirects() -> Dict[str, List[Tuple[bool, str, str]]]:
    """Validate all redirect endpoints"""
    results = {}
    
    print("🔄 Validating Backward Compatibility Redirects...")
    print("=" * 60)
    
    for category, endpoints in TEST_ENDPOINTS.items():
        print(f"\n📂 Testing {category.upper()} redirects:")
        results[category] = []
        
        for endpoint in endpoints:
            expected = EXPECTED_REDIRECTS.get(endpoint)
            success, message, location = test_redirect(endpoint, expected)
            results[category].append((success, message, location))
            print(f"   {message}")
    
    return results

def generate_summary(results: Dict[str, List[Tuple[bool, str, str]]]) -> Dict[str, int]:
    """Generate summary statistics"""
    summary = {
        "total_tests": 0,
        "successful_redirects": 0,
        "failed_redirects": 0,
        "missing_endpoints": 0
    }
    
    for category, tests in results.items():
        for success, message, location in tests:
            summary["total_tests"] += 1
            
            if success and "Redirect working" in message:
                summary["successful_redirects"] += 1
            elif "not found" in message:
                summary["missing_endpoints"] += 1
            else:
                summary["failed_redirects"] += 1
    
    return summary

def main():
    """Main validation function"""
    print("🚀 ISP Framework API Backward Compatibility Validation")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Run validation
    results = validate_all_redirects()
    
    # Generate summary
    summary = generate_summary(results)
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"✅ Successful Redirects: {summary['successful_redirects']}")
    print(f"❌ Failed Redirects: {summary['failed_redirects']}")
    print(f"🔍 Missing Endpoints: {summary['missing_endpoints']}")
    
    success_rate = (summary['successful_redirects'] / summary['total_tests']) * 100 if summary['total_tests'] > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Detailed recommendations
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDATIONS")
    print("=" * 60)
    
    if summary['failed_redirects'] > 0:
        print("❌ Some redirects are not working correctly:")
        print("   - Check endpoint file redirect implementations")
        print("   - Verify FastAPI router configuration")
        print("   - Ensure RedirectResponse imports are correct")
    
    if summary['missing_endpoints'] > 0:
        print("🔍 Some endpoints are missing:")
        print("   - Check if backend server is running")
        print("   - Verify endpoint registration in api.py")
        print("   - Check for import errors in endpoint files")
    
    if success_rate >= 90:
        print("✅ Excellent! Backward compatibility is working well.")
    elif success_rate >= 70:
        print("⚠️  Good, but some improvements needed.")
    else:
        print("❌ Significant issues found. Review implementation.")
    
    # Exit with appropriate code
    if summary['failed_redirects'] == 0 and summary['missing_endpoints'] == 0:
        print("\n🎉 All backward compatibility tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {summary['failed_redirects'] + summary['missing_endpoints']} issues found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
