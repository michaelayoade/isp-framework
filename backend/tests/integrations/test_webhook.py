"""Smoke tests for Webhook management endpoints.

Focus: basic create + list operations to verify the webhook module is
reachable and correctly persists data.
"""
import pytest


@pytest.mark.order(1)
def test_create_webhook(client):
    payload = {
        "name": "pytest-webhook",
        "url": "https://example.com/webhook",
        "secret": "pytest-secret",
        "events": ["customer.created"],
        "is_active": True,
    }
    resp = client.post("/api/v1/webhooks", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == payload["name"]
    assert data["url"] == payload["url"]


@pytest.mark.order(2)
def test_list_webhooks(client):
    resp = client.get("/api/v1/webhooks")
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert isinstance(result, list)
    assert any(w.get("name") == "pytest-webhook" for w in result)
import pytest
"""
Webhook Integration Test Script

This script tests the complete webhook integration across all ISP Framework modules.
Tests customer lifecycle events, billing events, service events, network events, and ticketing events.
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timezone
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookIntegrationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        self.access_token = None
        
    def authenticate(self, username: str = "admin", password: str = "admin123"):
        """Authenticate and get access token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password},
                headers=self.headers
            )
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                self.headers["Authorization"] = f"Bearer {self.access_token}"
                logger.info("✅ Authentication successful")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def test_webhook_endpoints(self):
        """Test webhook management endpoints"""
        logger.info("\n=== Testing Webhook Endpoints ===")
        
        # Test webhook registration
        webhook_data = {
            "name": "Test Webhook",
            "url": "https://webhook.site/unique-id",
            "secret": "test-secret-key",
            "events": [
                "customer.created",
                "invoice.created",
                "ticket.created",
                "service.activated"
            ],
            "is_active": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/webhooks",
                json=webhook_data,
                headers=self.headers
            )
            if response.status_code == 201:
                webhook = response.json()
                logger.info(f"✅ Webhook registered: {webhook['id']}")
                return webhook['id']
            else:
                logger.error(f"❌ Webhook registration failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Webhook registration error: {e}")
            return None
    
    def test_customer_webhooks(self):
        """Test customer-related webhook events"""
        logger.info("\n=== Testing Customer Webhooks ===")
        
        # Create test customer
        customer_data = {
            "full_name": "Test Customer Webhook",
            "email": "test.webhook@example.com",
            "phone": "+1234567890",
            "address": {
                "street_1": "123 Test St",
                "city": "Test City",
                "state": "Test State",
                "postal_code": "12345",
                "country": "US"
            },
            "status": "active"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/customers",
                json=customer_data,
                headers=self.headers
            )
            if response.status_code == 201:
                customer = response.json()
                logger.info(f"✅ Customer created: {customer['id']} (Portal ID: {customer['login']})")
                return customer['id']
            else:
                logger.error(f"❌ Customer creation failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Customer creation error: {e}")
            return None
    
    def test_billing_webhooks(self, customer_id: int):
        """Test billing-related webhook events"""
        logger.info("\n=== Testing Billing Webhooks ===")
        
        # Create billing account
        billing_account_data = {
            "customer_id": customer_id,
            "account_type": "customer",
            "billing_cycle": "monthly",
            "payment_method": "bank_transfer"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/billing/accounts",
                json=billing_account_data,
                headers=self.headers
            )
            if response.status_code == 201:
                account = response.json()
                logger.info(f"✅ Billing account created: {account['id']}")
                
                # Create invoice
                invoice_data = {
                    "billing_account_id": account['id'],
                    "total_amount": 99.99,
                    "currency": "USD",
                    "due_date": datetime.now(timezone.utc).isoformat(),
                    "items": [
                        {
                            "description": "Monthly Internet Service",
                            "quantity": 1,
                            "unit_price": 99.99,
                            "total_price": 99.99
                        }
                    ]
                }
                
                invoice_response = requests.post(
                    f"{self.base_url}/api/v1/billing/invoices",
                    json=invoice_data,
                    headers=self.headers
                )
                if invoice_response.status_code == 201:
                    invoice = invoice_response.json()
                    logger.info(f"✅ Invoice created: {invoice['invoice_number']}")
                    return invoice['id']
                else:
                    logger.error(f"❌ Invoice creation failed: {invoice_response.text}")
            else:
                logger.error(f"❌ Billing account creation failed: {response.text}")
        except Exception as e:
            logger.error(f"❌ Billing webhook test error: {e}")
        return None
    
    def test_ticketing_webhooks(self, customer_id: int):
        """Test ticketing-related webhook events"""
        logger.info("\n=== Testing Ticketing Webhooks ===")
        
        ticket_data = {
            "customer_id": customer_id,
            "title": "Test Webhook Ticket",
            "description": "Testing webhook integration for ticketing",
            "priority": "medium",
            "type": "technical",
            "source": "web"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/ticketing/tickets",
                json=ticket_data,
                headers=self.headers
            )
            if response.status_code == 201:
                ticket = response.json()
                logger.info(f"✅ Ticket created: {ticket['ticket_number']}")
                return ticket['id']
            else:
                logger.error(f"❌ Ticket creation failed: {response.text}")
        except Exception as e:
            logger.error(f"❌ Ticketing webhook test error: {e}")
        return None
    
    def test_service_webhooks(self, customer_id: int):
        """Test service-related webhook events"""
        logger.info("\n=== Testing Service Webhooks ===")
        
        # Create service plan first
        service_plan_data = {
            "title": "Test Webhook Service Plan",
            "service_type": "internet",
            "description": "Test plan for webhook integration",
            "monthly_price": 99.99,
            "setup_fee": 50.00,
            "is_active": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/service-plans",
                json=service_plan_data,
                headers=self.headers
            )
            if response.status_code == 201:
                service_plan = response.json()
                logger.info(f"✅ Service plan created: {service_plan['id']}")
                
                # Assign service to customer
                assignment_data = {
                    "customer_id": customer_id,
                    "service_plan_id": service_plan['id'],
                    "start_date": datetime.now(timezone.utc).isoformat(),
                    "status": "active"
                }
                
                assignment_response = requests.post(
                    f"{self.base_url}/api/v1/customer-services",
                    json=assignment_data,
                    headers=self.headers
                )
                if assignment_response.status_code == 201:
                    assignment = assignment_response.json()
                    logger.info(f"✅ Service assigned to customer: {assignment['id']}")
                    return assignment['id']
                else:
                    logger.error(f"❌ Service assignment failed: {assignment_response.text}")
            else:
                logger.error(f"❌ Service plan creation failed: {response.text}")
        except Exception as e:
            logger.error(f"❌ Service webhook test error: {e}")
        return None
    
    def test_webhook_delivery(self, webhook_id: str):
        """Test webhook delivery"""
        logger.info("\n=== Testing Webhook Delivery ===")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/webhooks/{webhook_id}/deliveries",
                headers=self.headers
            )
            if response.status_code == 200:
                deliveries = response.json()
                logger.info(f"✅ Found {len(deliveries)} webhook deliveries")
                for delivery in deliveries[:3]:  # Show first 3
                    logger.info(f"  - Delivery {delivery['id']}: {delivery['status']}")
                return True
            else:
                logger.error(f"❌ Webhook delivery check failed: {response.text}")
        except Exception as e:
            logger.error(f"❌ Webhook delivery check error: {e}")
        return False
    
    def run_all_tests(self):
        """Run all webhook integration tests"""
        logger.info("🚀 Starting Webhook Integration Tests")
        
        if not self.authenticate():
            return False
        
        # Test webhook registration
        webhook_id = self.test_webhook_endpoints()
        if not webhook_id:
            return False
        
        # Test customer webhooks
        customer_id = self.test_customer_webhooks()
        if not customer_id:
            return False
        
        # Test billing webhooks
        invoice_id = self.test_billing_webhooks(customer_id)
        
        # Test service webhooks
        service_assignment_id = self.test_service_webhooks(customer_id)
        
        # Test ticketing webhooks
        ticket_id = self.test_ticketing_webhooks(customer_id)
        
        # Test webhook delivery
        self.test_webhook_delivery(webhook_id)
        
        logger.info("\n🎉 Webhook Integration Tests Completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Webhook registered: {webhook_id}")
        logger.info(f"   - Customer created: {customer_id}")
        logger.info(f"   - Invoice created: {invoice_id}")
        logger.info(f"   - Service assigned: {service_assignment_id}")
        logger.info(f"   - Ticket created: {ticket_id}")
        
        return True

if __name__ == "__main__":
    tester = WebhookIntegrationTester()
    tester.run_all_tests()
