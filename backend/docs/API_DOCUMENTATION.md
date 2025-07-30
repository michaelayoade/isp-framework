# ISP Framework API Documentation

## Overview

The ISP Framework provides a comprehensive REST API for managing Internet Service Provider operations including customer management, service provisioning, billing automation, network monitoring, and administrative functions.

## Base URL

```
https://api.ispframework.com/v1
```

## Authentication

All API endpoints require authentication using JWT tokens or API keys:

### JWT Authentication (Admin/Reseller/Customer Portals)
```http
Authorization: Bearer <jwt_token>
```

### API Key Authentication (Reseller Integration)
```http
X-API-Key: <api_key>
```

## Rate Limiting

API requests are subject to rate limiting based on your subscription tier:

- **Free Tier**: 100 requests/minute, 10,000 requests/day
- **Professional**: 500 requests/minute, 50,000 requests/day  
- **Enterprise**: 2,000 requests/minute, 200,000 requests/day

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

The API uses conventional HTTP response codes and returns detailed error information:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## Core Business APIs

### Customer Management

#### Create Customer
```http
POST /customers
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345",
    "country": "US"
  },
  "billing_address": {
    "street": "123 Main St",
    "city": "Anytown", 
    "state": "CA",
    "zip": "12345",
    "country": "US"
  },
  "partner_id": 1
}
```

**Response:**
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "portal_id": "10003456",
  "status": "active",
  "created_at": "2025-01-29T10:30:00Z",
  "updated_at": "2025-01-29T10:30:00Z"
}
```

#### List Customers
```http
GET /customers?page=1&per_page=25&status=active&search=john
```

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 25, max: 100)
- `status` (string): Filter by status (active, suspended, terminated)
- `search` (string): Search by name, email, or phone
- `partner_id` (integer): Filter by partner/reseller

**Response:**
```json
{
  "customers": [
    {
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com",
      "status": "active",
      "created_at": "2025-01-29T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 150,
    "pages": 6
  }
}
```

### Service Management

#### Create Internet Service
```http
POST /customers/{customer_id}/services/internet
```

**Request Body:**
```json
{
  "plan_id": 1,
  "speed_download_mbps": 100,
  "speed_upload_mbps": 10,
  "data_limit_gb": null,
  "static_ip": false,
  "installation_address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345"
  },
  "scheduled_activation": "2025-02-01T09:00:00Z",
  "notes": "Customer requested morning installation"
}
```

**Response:**
```json
{
  "id": 456,
  "customer_id": 123,
  "service_type": "internet",
  "plan_id": 1,
  "status": "pending_activation",
  "speed_download_mbps": 100,
  "speed_upload_mbps": 10,
  "monthly_fee": 79.99,
  "activation_fee": 99.00,
  "created_at": "2025-01-29T10:30:00Z",
  "scheduled_activation": "2025-02-01T09:00:00Z"
}
```

#### Provision Service
```http
POST /services/{service_id}/provision
```

**Request Body:**
```json
{
  "provisioning_data": {
    "router_id": 1,
    "vlan_id": 100,
    "ip_assignment": "192.168.1.100/24",
    "bandwidth_profile": "100M_10M"
  },
  "priority": "normal",
  "scheduled_time": "2025-02-01T09:00:00Z"
}
```

**Response:**
```json
{
  "provisioning_job_id": 789,
  "service_id": 456,
  "status": "queued",
  "priority": "normal",
  "estimated_completion": "2025-02-01T09:30:00Z",
  "created_at": "2025-01-29T10:30:00Z"
}
```

### Billing Management

#### Generate Invoice
```http
POST /billing/invoices
```

**Request Body:**
```json
{
  "customer_id": 123,
  "invoice_type": "recurring",
  "billing_period": {
    "start_date": "2025-02-01",
    "end_date": "2025-02-28"
  },
  "line_items": [
    {
      "service_id": 456,
      "description": "Internet Service - 100/10 Mbps",
      "amount": 79.99,
      "quantity": 1,
      "proration_factor": 1.0
    }
  ],
  "due_date": "2025-02-15"
}
```

**Response:**
```json
{
  "id": 789,
  "customer_id": 123,
  "invoice_number": "INV-2025-000789",
  "subtotal": 79.99,
  "tax_amount": 6.40,
  "total_amount": 86.39,
  "due_date": "2025-02-15",
  "status": "pending",
  "created_at": "2025-01-29T10:30:00Z"
}
```

## Monitoring & Operations APIs

### SLA Monitoring

#### Check SLA Breaches
```http
POST /sla/check-breaches
```

**Response:**
```json
{
  "breached_tickets": [
    {
      "ticket_id": 123,
      "customer_id": 456,
      "breach_time": "2025-01-29T08:00:00Z",
      "overdue_minutes": 120
    }
  ],
  "warnings_issued": [
    {
      "ticket_id": 124,
      "customer_id": 457,
      "time_remaining_minutes": 15
    }
  ],
  "total_checked": 25,
  "check_time": "2025-01-29T10:30:00Z"
}
```

#### Get SLA Performance Metrics
```http
GET /sla/performance-metrics?period_days=30
```

**Response:**
```json
{
  "period_start": "2024-12-30T10:30:00Z",
  "period_end": "2025-01-29T10:30:00Z",
  "period_days": 30,
  "total_tickets": 100,
  "tickets_within_sla": 85,
  "tickets_breached": 15,
  "sla_compliance_rate": 85.0,
  "average_resolution_time_minutes": 180,
  "escalation_rate": 12.0,
  "by_priority": {
    "critical": {
      "total": 10,
      "within_sla": 8,
      "compliance_rate": 80.0
    },
    "high": {
      "total": 25,
      "within_sla": 20,
      "compliance_rate": 80.0
    }
  }
}
```

### API Quota Management

#### Check Rate Limit
```http
GET /api-quota/rate-limit/check/{api_key}?endpoint=/customers
```

**Response:**
```json
{
  "allowed": true,
  "remaining_calls": {
    "60s": 95,
    "3600s": 950
  },
  "reset_time": "2025-01-29T11:00:00Z"
}
```

#### Get Usage Analytics
```http
GET /api-quota/analytics/{api_key}?period_days=30
```

**Response:**
```json
{
  "api_key": "isp_abc123...",
  "reseller_id": 1,
  "period_start": "2024-12-30T10:30:00Z",
  "period_end": "2025-01-29T10:30:00Z",
  "period_days": 30,
  "analytics": {
    "total_calls": 45000,
    "average_calls_per_day": 1500,
    "success_rate": 98.5,
    "most_used_endpoints": [
      {
        "endpoint": "/customers",
        "calls": 15000
      },
      {
        "endpoint": "/services",
        "calls": 12000
      }
    ],
    "error_rate_by_endpoint": {
      "/customers": 1.2,
      "/services": 2.1
    }
  }
}
```

### Plugin Health Monitoring

#### Perform Health Checks
```http
POST /plugins/health/check-all
```

**Response:**
```json
{
  "overall_status": "healthy",
  "total_plugins": 5,
  "healthy_plugins": 4,
  "warning_plugins": 1,
  "critical_plugins": 0,
  "offline_plugins": 0,
  "check_time": "2025-01-29T10:30:00Z",
  "plugin_results": [
    {
      "plugin_id": 1,
      "plugin_name": "Payment Gateway",
      "status": "healthy",
      "checks": {
        "process": {
          "status": "healthy",
          "running": true,
          "uptime_seconds": 3600
        },
        "api": {
          "status": "healthy",
          "response_time_ms": 150
        }
      },
      "metrics": {
        "requests_per_minute": 45,
        "error_rate_percent": 0.5
      }
    }
  ]
}
```

#### Reload Plugin
```http
POST /plugins/{plugin_id}/reload
```

**Response:**
```json
{
  "plugin_id": 1,
  "plugin_name": "Payment Gateway",
  "reload_time": "2025-01-29T10:30:00Z",
  "health_status": "healthy",
  "success": true
}
```

## Webhook Events

The ISP Framework sends webhook notifications for various events. Configure webhook endpoints in your admin panel.

### Webhook Headers
```http
X-ISP-Event: customer.created
X-ISP-Signature: sha256=<signature>
Content-Type: application/json
```

### Event Types

#### Customer Events
- `customer.created`
- `customer.updated`
- `customer.suspended`
- `customer.reactivated`

#### Service Events
- `service.created`
- `service.activated`
- `service.suspended`
- `service.terminated`

#### Billing Events
- `invoice.generated`
- `payment.received`
- `payment.failed`
- `payment.overdue`

#### System Events
- `sla.breached`
- `plugin.failed`
- `quota.exceeded`

### Example Webhook Payload
```json
{
  "event": "customer.created",
  "timestamp": "2025-01-29T10:30:00Z",
  "data": {
    "customer_id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "portal_id": "10003456",
    "partner_id": 1
  }
}
```

## SDKs and Libraries

### Official SDKs
- **Python**: `pip install isp-framework-python`
- **JavaScript/Node.js**: `npm install isp-framework-js`
- **PHP**: `composer require isp-framework/php-sdk`

### Example Usage (Python)
```python
from isp_framework import ISPClient

client = ISPClient(api_key='your_api_key')

# Create customer
customer = client.customers.create({
    'name': 'John Doe',
    'email': 'john@example.com',
    'phone': '+1234567890'
})

# Create internet service
service = client.services.create_internet(customer.id, {
    'plan_id': 1,
    'speed_download_mbps': 100,
    'speed_upload_mbps': 10
})
```

## Testing

### Sandbox Environment
Use the sandbox environment for testing:
```
https://sandbox-api.ispframework.com/v1
```

### Test API Keys
Sandbox API keys are prefixed with `test_`:
```
X-API-Key: test_isp_abc123...
```

### Test Data
The sandbox includes pre-populated test data:
- Test customers with IDs 1-100
- Sample service plans and configurations
- Mock payment processing

## Support

### Documentation
- **API Reference**: https://docs.ispframework.com/api
- **Guides**: https://docs.ispframework.com/guides
- **Examples**: https://github.com/ispframework/examples

### Support Channels
- **Email**: api-support@ispframework.com
- **Discord**: https://discord.gg/ispframework
- **GitHub Issues**: https://github.com/ispframework/api-issues

### Status Page
Monitor API status and incidents: https://status.ispframework.com

## Changelog

### v1.3.0 (2025-01-29)
- Added SLA monitoring and escalation APIs
- Implemented API quota management and rate limiting
- Added plugin health monitoring endpoints
- Enhanced webhook event coverage
- Improved error handling and validation

### v1.2.0 (2025-01-15)
- Added service-specific endpoints (Internet, Voice, Bundle)
- Implemented async provisioning queue
- Added billing automation features
- Enhanced RBAC and row-level security

### v1.1.0 (2024-12-15)
- Added customer portal authentication
- Implemented reseller management
- Added network device management
- Enhanced audit logging

### v1.0.0 (2024-11-01)
- Initial API release
- Core customer and service management
- Basic billing functionality
- Authentication and authorization
