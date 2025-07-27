# API Flow Examples - Real-World Usage Patterns

This guide demonstrates complete API workflows using realistic examples that show how endpoints work together to accomplish business objectives. Each flow includes sample payloads, responses, error handling, and next steps.

## 🎯 Customer Onboarding Journey

### Overview
Complete customer onboarding from account creation to service activation, including network provisioning and billing setup.

### Flow Diagram
```
Customer Registration → Service Selection → Network Provisioning → Payment Setup → Service Activation
       ↓                      ↓                    ↓                   ↓               ↓
   POST /customers    POST /subscriptions    POST /devices      POST /payments    GET /services/status
```

---

## Step 1: Create Customer Account

**Endpoint**: `POST /api/v1/customers`

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/customers" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sarah Johnson",
    "email": "sarah.johnson@email.com",
    "phone": "+1-555-0123",
    "address": {
      "street": "123 Main Street",
      "city": "Springfield",
      "state": "IL",
      "zip_code": "62701",
      "country": "US"
    },
    "business_info": {
      "company_name": "Johnson Consulting LLC",
      "tax_id": "12-3456789",
      "business_type": "LLC"
    },
    "preferences": {
      "communication_method": "email",
      "billing_cycle": "monthly",
      "auto_pay": true
    }
  }'
```

### Response (201 Created)
```json
{
  "id": 12345,
  "portal_id": "ISP0012345",
  "name": "Sarah Johnson",
  "email": "sarah.johnson@email.com",
  "phone": "+1-555-0123",
  "status": "active",
  "customer_type": "business",
  "address": {
    "id": 67890,
    "street": "123 Main Street",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "country": "US"
  },
  "business_info": {
    "company_name": "Johnson Consulting LLC",
    "tax_id": "12-3456789",
    "business_type": "LLC"
  },
  "preferences": {
    "communication_method": "email",
    "billing_cycle": "monthly",
    "auto_pay": true
  },
  "created_at": "2025-01-26T10:30:00Z",
  "updated_at": "2025-01-26T10:30:00Z"
}
```

### Key Data for Next Steps
- **Customer ID**: `12345`
- **Portal ID**: `ISP0012345`
- **Address ID**: `67890`

---

## Step 2: Add Internet Service Subscription

**Endpoint**: `POST /api/v1/customers/12345/services`

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/customers/12345/services" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "internet",
    "plan_id": "fiber-100",
    "service_details": {
      "download_speed": 100,
      "upload_speed": 100,
      "data_limit": null,
      "technology": "fiber",
      "static_ip": true,
      "ip_count": 1
    },
    "installation": {
      "preferred_date": "2025-02-01",
      "time_window": "morning",
      "special_instructions": "Business hours only, contact office manager"
    },
    "billing": {
      "monthly_rate": 89.99,
      "setup_fee": 99.00,
      "contract_term": 12,
      "auto_pay": true
    }
  }'
```

### Response (201 Created)
```json
{
  "id": 54321,
  "customer_id": 12345,
  "service_type": "internet",
  "plan_id": "fiber-100",
  "status": "pending_installation",
  "service_details": {
    "download_speed": 100,
    "upload_speed": 100,
    "data_limit": null,
    "technology": "fiber",
    "static_ip": true,
    "ip_count": 1,
    "assigned_ips": []
  },
  "installation": {
    "scheduled_date": "2025-02-01T09:00:00Z",
    "technician_id": 789,
    "time_window": "morning",
    "special_instructions": "Business hours only, contact office manager",
    "status": "scheduled"
  },
  "billing": {
    "monthly_rate": 89.99,
    "setup_fee": 99.00,
    "contract_term": 12,
    "contract_start": null,
    "next_billing_date": null,
    "auto_pay": true
  },
  "created_at": "2025-01-26T10:35:00Z",
  "updated_at": "2025-01-26T10:35:00Z"
}
```

### Key Data for Next Steps
- **Service ID**: `54321`
- **Installation Date**: `2025-02-01T09:00:00Z`
- **Technician ID**: `789`

---

## Step 3: Provision Network Device

**Endpoint**: `POST /api/v1/network/devices`

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/network/devices" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 12345,
    "service_id": 54321,
    "device_type": "ont",
    "model": "Nokia G-010G-A",
    "serial_number": "NKIA123456789",
    "mac_address": "00:1A:2B:3C:4D:5E",
    "location": {
      "address_id": 67890,
      "installation_notes": "Basement utility room, left wall"
    },
    "network_config": {
      "vlan": 100,
      "bandwidth_profile": "fiber-100mbps",
      "qos_profile": "business"
    }
  }'
```

### Response (201 Created)
```json
{
  "id": 98765,
  "customer_id": 12345,
  "service_id": 54321,
  "device_type": "ont",
  "model": "Nokia G-010G-A",
  "serial_number": "NKIA123456789",
  "mac_address": "00:1A:2B:3C:4D:5E",
  "status": "provisioned",
  "location": {
    "address_id": 67890,
    "installation_notes": "Basement utility room, left wall",
    "coordinates": {
      "latitude": 39.7817,
      "longitude": -89.6501
    }
  },
  "network_config": {
    "vlan": 100,
    "bandwidth_profile": "fiber-100mbps",
    "qos_profile": "business",
    "assigned_ip": "192.168.100.45",
    "gateway": "192.168.100.1",
    "dns_servers": ["8.8.8.8", "8.8.4.4"]
  },
  "provisioning": {
    "provisioned_at": "2025-01-26T10:40:00Z",
    "provisioned_by": "system",
    "configuration_pushed": true,
    "activation_pending": true
  },
  "created_at": "2025-01-26T10:40:00Z",
  "updated_at": "2025-01-26T10:40:00Z"
}
```

### Key Data for Next Steps
- **Device ID**: `98765`
- **Assigned IP**: `192.168.100.45`
- **Status**: `provisioned`

---

## Step 4: Set Up Payment Method

**Endpoint**: `POST /api/v1/customers/12345/payment-methods`

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/customers/12345/payment-methods" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit_card",
    "card_details": {
      "number": "4111111111111111",
      "expiry_month": 12,
      "expiry_year": 2027,
      "cvv": "123",
      "cardholder_name": "Sarah Johnson"
    },
    "billing_address": {
      "street": "123 Main Street",
      "city": "Springfield",
      "state": "IL",
      "zip_code": "62701",
      "country": "US"
    },
    "is_default": true,
    "auto_pay": true
  }'
```

### Response (201 Created)
```json
{
  "id": 11111,
  "customer_id": 12345,
  "type": "credit_card",
  "card_details": {
    "last_four": "1111",
    "brand": "visa",
    "expiry_month": 12,
    "expiry_year": 2027,
    "cardholder_name": "Sarah Johnson"
  },
  "billing_address": {
    "street": "123 Main Street",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
    "country": "US"
  },
  "status": "active",
  "is_default": true,
  "auto_pay": true,
  "created_at": "2025-01-26T10:45:00Z",
  "verified_at": "2025-01-26T10:45:00Z"
}
```

### Key Data for Next Steps
- **Payment Method ID**: `11111`
- **Status**: `active`
- **Auto Pay**: `enabled`

---

## Step 5: Process Initial Payment

**Endpoint**: `POST /api/v1/payments`

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 12345,
    "payment_method_id": 11111,
    "amount": 188.99,
    "currency": "USD",
    "description": "Setup fee and first month service",
    "invoice_items": [
      {
        "description": "Fiber Internet 100/100 - First Month",
        "amount": 89.99,
        "service_id": 54321
      },
      {
        "description": "Installation and Setup Fee",
        "amount": 99.00,
        "service_id": 54321
      }
    ],
    "metadata": {
      "service_activation": true,
      "installation_payment": true
    }
  }'
```

### Response (201 Created)
```json
{
  "id": 22222,
  "customer_id": 12345,
  "payment_method_id": 11111,
  "amount": 188.99,
  "currency": "USD",
  "status": "succeeded",
  "description": "Setup fee and first month service",
  "transaction_id": "txn_1234567890abcdef",
  "gateway_response": {
    "gateway": "stripe",
    "charge_id": "ch_1234567890abcdef",
    "receipt_url": "https://pay.stripe.com/receipts/..."
  },
  "invoice_items": [
    {
      "description": "Fiber Internet 100/100 - First Month",
      "amount": 89.99,
      "service_id": 54321
    },
    {
      "description": "Installation and Setup Fee",
      "amount": 99.00,
      "service_id": 54321
    }
  ],
  "processed_at": "2025-01-26T10:50:00Z",
  "created_at": "2025-01-26T10:50:00Z"
}
```

### Key Data for Next Steps
- **Payment ID**: `22222`
- **Transaction ID**: `txn_1234567890abcdef`
- **Status**: `succeeded`

---

## Step 6: Check Service Activation Status

**Endpoint**: `GET /api/v1/services/54321/status`

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/services/54321/status" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Response (200 OK)
```json
{
  "service_id": 54321,
  "customer_id": 12345,
  "status": "active",
  "activation_details": {
    "activated_at": "2025-01-26T10:51:00Z",
    "activated_by": "payment_processor",
    "activation_trigger": "payment_received"
  },
  "service_health": {
    "connectivity": "online",
    "last_seen": "2025-01-26T10:55:00Z",
    "uptime_percentage": 100.0,
    "speed_test": {
      "download_mbps": 98.5,
      "upload_mbps": 97.2,
      "latency_ms": 12,
      "tested_at": "2025-01-26T10:52:00Z"
    }
  },
  "network_details": {
    "device_id": 98765,
    "assigned_ips": ["203.0.113.45"],
    "vlan": 100,
    "bandwidth_usage": {
      "current_download_mbps": 15.2,
      "current_upload_mbps": 3.1,
      "monthly_usage_gb": 0.1
    }
  },
  "billing_status": {
    "next_billing_date": "2025-02-26T00:00:00Z",
    "current_balance": 0.00,
    "auto_pay_enabled": true
  }
}
```

---

## 🎉 Customer Onboarding Complete!

**Summary of Created Resources:**
- ✅ Customer Account: `12345` (Portal ID: `ISP0012345`)
- ✅ Internet Service: `54321` (100/100 Mbps Fiber)
- ✅ Network Device: `98765` (Nokia ONT)
- ✅ Payment Method: `11111` (Visa ending in 1111)
- ✅ Initial Payment: `22222` ($188.99 processed)
- ✅ Service Status: `active` (98.5/97.2 Mbps tested)

---

## 💰 Billing Journey Examples

### Get Customer Invoices

**Endpoint**: `GET /api/v1/customers/12345/invoices`

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/customers/12345/invoices?status=unpaid&limit=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Response (200 OK)
```json
{
  "data": [
    {
      "id": 33333,
      "customer_id": 12345,
      "invoice_number": "INV-2025-001234",
      "status": "unpaid",
      "amount_due": 89.99,
      "currency": "USD",
      "due_date": "2025-02-26T23:59:59Z",
      "billing_period": {
        "start": "2025-02-01T00:00:00Z",
        "end": "2025-02-28T23:59:59Z"
      },
      "line_items": [
        {
          "description": "Fiber Internet 100/100 - February 2025",
          "service_id": 54321,
          "amount": 89.99,
          "quantity": 1,
          "unit_price": 89.99
        }
      ],
      "issued_at": "2025-02-01T00:00:00Z",
      "created_at": "2025-02-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

### Pay Invoice

**Endpoint**: `POST /api/v1/invoices/33333/pay`

### Request
```bash
curl -X POST "http://localhost:8000/api/v1/invoices/33333/pay" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method_id": 11111,
    "amount": 89.99
  }'
```

### Response (200 OK)
```json
{
  "payment_id": 44444,
  "invoice_id": 33333,
  "amount": 89.99,
  "status": "succeeded",
  "transaction_id": "txn_abcdef1234567890",
  "processed_at": "2025-02-15T14:30:00Z",
  "receipt": {
    "url": "https://pay.stripe.com/receipts/...",
    "email_sent": true
  }
}
```

### Verify Payment

**Endpoint**: `GET /api/v1/payments/44444`

### Request
```bash
curl -X GET "http://localhost:8000/api/v1/payments/44444" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Response (200 OK)
```json
{
  "id": 44444,
  "customer_id": 12345,
  "invoice_id": 33333,
  "payment_method_id": 11111,
  "amount": 89.99,
  "currency": "USD",
  "status": "succeeded",
  "description": "Invoice payment - INV-2025-001234",
  "transaction_id": "txn_abcdef1234567890",
  "gateway_response": {
    "gateway": "stripe",
    "charge_id": "ch_abcdef1234567890",
    "receipt_url": "https://pay.stripe.com/receipts/..."
  },
  "processed_at": "2025-02-15T14:30:00Z",
  "created_at": "2025-02-15T14:30:00Z",
  "refunds": [],
  "metadata": {
    "auto_pay": false,
    "manual_payment": true
  }
}
```

---

## ⚠️ Error Handling in API Flows

### Failed Payment Scenario

When a payment fails during the onboarding flow, the system handles it gracefully:

#### Payment Failure Response (402 Payment Required)
```json
{
  "type": "https://ispframework.com/errors/payment",
  "title": "Payment Failed",
  "status": 402,
  "detail": "Your card was declined. Please try a different payment method.",
  "instance": "/api/v1/payments",
  "error_id": "pay_error_123456",
  "timestamp": "2025-01-26T10:50:00Z",
  "context": {
    "gateway_error": "card_declined",
    "decline_code": "insufficient_funds",
    "payment_method_id": 11111
  },
  "suggested_actions": [
    "Try a different payment method",
    "Contact your bank",
    "Update card information"
  ]
}
```

#### Service Status After Payment Failure
```bash
curl -X GET "http://localhost:8000/api/v1/services/54321/status"
```

```json
{
  "service_id": 54321,
  "status": "payment_pending",
  "activation_blocked": {
    "reason": "payment_required",
    "amount_due": 188.99,
    "retry_payment_url": "/api/v1/payments/retry/22222"
  },
  "grace_period": {
    "expires_at": "2025-01-28T10:50:00Z",
    "days_remaining": 2
  }
}
```

### Rate Limiting Response (429 Too Many Requests)
```json
{
  "type": "https://ispframework.com/errors/rate-limit",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please wait before trying again.",
  "instance": "/api/v1/customers",
  "retry_after": 3600,
  "limit": {
    "requests": 1000,
    "window": "1 hour",
    "remaining": 0,
    "reset_at": "2025-01-26T12:00:00Z"
  }
}
```

### Validation Error Response (400 Bad Request)
```json
{
  "type": "https://ispframework.com/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "The request contains invalid data",
  "instance": "/api/v1/customers",
  "errors": [
    {
      "field": "email",
      "code": "invalid_format",
      "message": "Email address is not valid"
    },
    {
      "field": "phone",
      "code": "invalid_format",
      "message": "Phone number must include country code"
    }
  ]
}
```

---

## 🔄 Flow Continuity Best Practices

### 1. Use Consistent IDs
Always use the same customer_id, service_id, and other identifiers throughout the flow to maintain data consistency.

### 2. Check Status Before Proceeding
Before each major step, verify the current status:
```bash
# Check customer status
GET /api/v1/customers/12345

# Check service status
GET /api/v1/services/54321/status

# Check payment status
GET /api/v1/payments/22222
```

### 3. Handle Async Operations
Some operations (like device provisioning) are asynchronous. Use webhooks or polling:

```bash
# Poll for completion
while true; do
  status=$(curl -s "http://localhost:8000/api/v1/devices/98765/status" | jq -r '.status')
  if [ "$status" = "active" ]; then
    echo "Device provisioning complete"
    break
  fi
  sleep 5
done
```

### 4. Implement Idempotency
Use idempotency keys for critical operations:
```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Idempotency-Key: payment_12345_setup_20250126" \
  -H "Content-Type: application/json" \
  -d '...'
```

---

## 📊 Visual Flow Summary

```mermaid
graph TD
    A[Create Customer] --> B[Add Service]
    B --> C[Provision Device]
    C --> D[Setup Payment]
    D --> E[Process Payment]
    E --> F{Payment Success?}
    F -->|Yes| G[Activate Service]
    F -->|No| H[Payment Failed]
    H --> I[Grace Period]
    I --> J[Retry Payment]
    J --> F
    G --> K[Service Active]
    
    style A fill:#e1f5fe
    style G fill:#c8e6c9
    style H fill:#ffcdd2
    style K fill:#4caf50
```

This comprehensive flow documentation provides developers with real-world examples they can follow to integrate with the ISP Framework API effectively. Each step builds on the previous one, showing how data flows through the system and how to handle both success and error scenarios.
