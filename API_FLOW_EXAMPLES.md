# 🚀 **ISP Framework API Flow Examples**

## **📋 Overview**

This document provides **real-world flow-based API usage examples** for the ISP Framework, showing complete customer journeys with sample payloads, responses, and error handling.

---

## **🎯 Flow 1: Complete Customer Onboarding Journey**

### **Business Scenario**
New customer "John Doe" wants to sign up for internet service. The flow covers account creation, service selection, provisioning, and activation.

### **Step 1: Create Customer Account**
```http
POST /api/v1/customers/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "address": "123 Main Street",
  "city": "Lagos",
  "state": "Lagos",
  "postal_code": "100001",
  "country": "Nigeria",
  "account_type": "residential",
  "preferred_language": "en"
}
```

**Response:**
```json
{
  "id": "cust_12345",
  "portal_id": "10012345",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "status": "active",
  "account_type": "residential",
  "created_at": "2025-01-26T21:46:57Z",
  "billing_config": {
    "billing_cycle": "monthly",
    "payment_method": null,
    "auto_pay": false
  }
}
```

### **Step 2: Browse Available Service Templates**
```http
GET /api/v1/services/templates/internet?location=Lagos&status=active
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "templates": [
    {
      "id": "tmpl_fiber_50",
      "name": "Fiber 50Mbps",
      "service_type": "internet",
      "download_speed": 50,
      "upload_speed": 25,
      "data_limit": null,
      "monthly_price": 15000,
      "setup_fee": 5000,
      "available_locations": ["Lagos", "Abuja"],
      "features": ["Static IP", "24/7 Support", "No FUP"]
    },
    {
      "id": "tmpl_fiber_100",
      "name": "Fiber 100Mbps", 
      "service_type": "internet",
      "download_speed": 100,
      "upload_speed": 50,
      "data_limit": null,
      "monthly_price": 25000,
      "setup_fee": 5000,
      "available_locations": ["Lagos", "Abuja"],
      "features": ["Static IP", "24/7 Support", "No FUP", "Priority Support"]
    }
  ]
}
```

### **Step 3: Create Service Subscription**
```http
POST /api/v1/services/subscriptions/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "template_id": "tmpl_fiber_50",
  "installation_address": {
    "address": "123 Main Street",
    "city": "Lagos",
    "state": "Lagos",
    "postal_code": "100001"
  },
  "preferred_installation_date": "2025-01-30",
  "notes": "Customer prefers morning installation"
}
```

**Response:**
```json
{
  "id": "sub_67890",
  "customer_id": "cust_12345",
  "template_id": "tmpl_fiber_50",
  "status": "pending_provisioning",
  "monthly_price": 15000,
  "setup_fee": 5000,
  "activation_date": null,
  "next_billing_date": null,
  "created_at": "2025-01-26T21:47:15Z",
  "provisioning": {
    "status": "queued",
    "estimated_completion": "2025-01-30T10:00:00Z"
  }
}
```

### **Step 4: Provision Network Resources**
```http
POST /api/v1/services/provisioning/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "subscription_id": "sub_67890",
  "template_id": "prov_tmpl_fiber",
  "priority": "normal",
  "automation_level": "full",
  "configuration": {
    "router_id": "router_lag_001",
    "sector_id": "sector_lag_001_a",
    "speed_profile": "50M_25M",
    "ip_pool": "residential_pool_1"
  }
}
```

**Response:**
```json
{
  "id": "prov_11111",
  "subscription_id": "sub_67890",
  "status": "in_progress",
  "progress": 25,
  "estimated_completion": "2025-01-30T10:00:00Z",
  "tasks": [
    {
      "id": "task_ip_assign",
      "name": "IP Address Assignment",
      "status": "completed",
      "result": {
        "ip_address": "192.168.100.50",
        "gateway": "192.168.100.1",
        "dns": ["8.8.8.8", "8.8.4.4"]
      }
    },
    {
      "id": "task_radius_user",
      "name": "RADIUS User Creation",
      "status": "in_progress",
      "progress": 75
    },
    {
      "id": "task_router_config",
      "name": "Router Configuration",
      "status": "pending"
    }
  ]
}
```

### **Step 5: Generate Initial Invoice**
```http
POST /api/v1/billing/invoices/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "subscription_id": "sub_67890",
  "invoice_type": "setup",
  "items": [
    {
      "description": "Fiber 50Mbps - Setup Fee",
      "amount": 5000,
      "quantity": 1
    },
    {
      "description": "Fiber 50Mbps - First Month",
      "amount": 15000,
      "quantity": 1
    }
  ],
  "due_date": "2025-02-02"
}
```

**Response:**
```json
{
  "id": "inv_22222",
  "customer_id": "cust_12345",
  "invoice_number": "INV-2025-001",
  "status": "pending",
  "total_amount": 20000,
  "due_date": "2025-02-02",
  "items": [
    {
      "description": "Fiber 50Mbps - Setup Fee",
      "amount": 5000,
      "quantity": 1
    },
    {
      "description": "Fiber 50Mbps - First Month", 
      "amount": 15000,
      "quantity": 1
    }
  ],
  "payment_link": "https://pay.ispframework.com/inv_22222"
}
```

### **Step 6: Process Payment**
```http
POST /api/v1/billing/payments/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "invoice_id": "inv_22222",
  "amount": 20000,
  "payment_method": "bank_transfer",
  "reference": "TXN123456789",
  "notes": "Payment via online banking"
}
```

**Response:**
```json
{
  "id": "pay_33333",
  "customer_id": "cust_12345",
  "invoice_id": "inv_22222",
  "amount": 20000,
  "status": "completed",
  "payment_method": "bank_transfer",
  "reference": "TXN123456789",
  "processed_at": "2025-01-26T21:48:30Z",
  "invoice_status": "paid"
}
```

### **Step 7: Check Service Status**
```http
GET /api/v1/services/subscriptions/sub_67890
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "id": "sub_67890",
  "customer_id": "cust_12345",
  "status": "active",
  "service_details": {
    "ip_address": "192.168.100.50",
    "username": "10012345",
    "password": "generated_password_123",
    "connection_type": "pppoe"
  },
  "provisioning": {
    "status": "completed",
    "completed_at": "2025-01-30T09:45:00Z"
  },
  "billing": {
    "next_billing_date": "2025-02-26",
    "monthly_amount": 15000
  }
}
```

---

## **💳 Flow 2: Monthly Billing Journey**

### **Business Scenario**
Existing customer's monthly billing cycle - invoice generation, payment processing, and service continuity.

### **Step 1: Get Customer Invoices**
```http
GET /api/v1/billing/customers/cust_12345/invoices?status=pending&limit=5
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "invoices": [
    {
      "id": "inv_44444",
      "invoice_number": "INV-2025-025",
      "status": "pending",
      "total_amount": 15000,
      "due_date": "2025-02-26",
      "service_period": {
        "start": "2025-02-26",
        "end": "2025-03-26"
      },
      "items": [
        {
          "description": "Fiber 50Mbps - Monthly Service",
          "amount": 15000,
          "quantity": 1
        }
      ]
    }
  ],
  "total_outstanding": 15000
}
```

### **Step 2: Process Payment**
```http
POST /api/v1/billing/payments/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "invoice_id": "inv_44444",
  "amount": 15000,
  "payment_method": "card",
  "card_details": {
    "last_four": "1234",
    "brand": "visa"
  },
  "reference": "CARD_TXN_789012"
}
```

**Response:**
```json
{
  "id": "pay_55555",
  "customer_id": "cust_12345",
  "invoice_id": "inv_44444",
  "amount": 15000,
  "status": "completed",
  "payment_method": "card",
  "reference": "CARD_TXN_789012",
  "processed_at": "2025-02-25T14:30:00Z"
}
```

### **Step 3: Verify Payment Status**
```http
GET /api/v1/billing/payments/pay_55555
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "id": "pay_55555",
  "customer_id": "cust_12345",
  "invoice_id": "inv_44444",
  "amount": 15000,
  "status": "completed",
  "payment_method": "card",
  "reference": "CARD_TXN_789012",
  "processed_at": "2025-02-25T14:30:00Z",
  "invoice": {
    "id": "inv_44444",
    "status": "paid",
    "paid_at": "2025-02-25T14:30:00Z"
  },
  "service_impact": {
    "subscription_id": "sub_67890",
    "status": "active",
    "next_billing_date": "2025-03-26"
  }
}
```

---

## **🚨 Flow 3: Error Handling & Recovery**

### **Scenario 1: Failed Payment Impact on Service**

#### **Failed Payment Attempt**
```http
POST /api/v1/billing/payments/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "invoice_id": "inv_66666",
  "amount": 15000,
  "payment_method": "card",
  "card_token": "invalid_token_123"
}
```

**Error Response:**
```json
{
  "error": {
    "code": "PAYMENT_FAILED",
    "message": "Payment processing failed",
    "details": {
      "reason": "invalid_card_token",
      "gateway_response": "Token not found",
      "retry_allowed": true,
      "retry_after": 300
    }
  },
  "invoice": {
    "id": "inv_66666",
    "status": "overdue",
    "days_overdue": 3,
    "grace_period_remaining": 4
  },
  "service_impact": {
    "subscription_id": "sub_67890",
    "status": "active",
    "suspension_scheduled": "2025-03-05T00:00:00Z",
    "warning_sent": true
  }
}
```

#### **Check Service Status After Failed Payment**
```http
GET /api/v1/services/subscriptions/sub_67890
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "id": "sub_67890",
  "status": "active_with_warning",
  "suspension": {
    "scheduled_at": "2025-03-05T00:00:00Z",
    "reason": "overdue_payment",
    "grace_period_remaining": "4 days",
    "can_prevent": true
  },
  "billing": {
    "outstanding_amount": 15000,
    "overdue_invoices": 1,
    "last_payment_attempt": "2025-03-01T10:15:00Z",
    "last_payment_status": "failed"
  }
}
```

### **Scenario 2: Rate Limiting**

#### **Too Many Requests**
```http
POST /api/v1/billing/payments/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json
```

**Rate Limit Response:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many payment attempts",
    "details": {
      "limit": 5,
      "window": "1 hour",
      "reset_at": "2025-03-01T11:00:00Z",
      "retry_after": 1800
    }
  }
}
```

### **Scenario 3: Validation Errors**

#### **Invalid Customer Data**
```http
POST /api/v1/customers/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "first_name": "",
  "email": "invalid-email",
  "phone": "123"
}
```

**Validation Error Response:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field_errors": [
        {
          "field": "first_name",
          "message": "First name is required",
          "code": "required"
        },
        {
          "field": "email",
          "message": "Invalid email format",
          "code": "invalid_format"
        },
        {
          "field": "phone",
          "message": "Phone number must be at least 10 digits",
          "code": "min_length"
        }
      ]
    }
  }
}
```

---

## **📊 Flow 4: Customer Self-Service Portal Journey**

### **Customer Login & Dashboard**
```http
POST /api/v1/customers/auth/login
Content-Type: application/json

{
  "portal_id": "10012345",
  "password": "customer_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "customer": {
    "id": "cust_12345",
    "portal_id": "10012345",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### **View Service Usage**
```http
GET /api/v1/customers/services/usage?period=current_month
Authorization: Bearer {customer_jwt_token}
```

**Response:**
```json
{
  "usage_summary": {
    "period": "2025-02",
    "services": [
      {
        "subscription_id": "sub_67890",
        "service_name": "Fiber 50Mbps",
        "usage": {
          "download_gb": 245.5,
          "upload_gb": 89.2,
          "total_gb": 334.7,
          "sessions": 156,
          "peak_speed_mbps": 48.9
        },
        "limits": {
          "data_limit": null,
          "speed_limit": "50 Mbps"
        }
      }
    ]
  }
}
```

### **Request Service Upgrade**
```http
POST /api/v1/customers/services/requests
Authorization: Bearer {customer_jwt_token}
Content-Type: application/json

{
  "subscription_id": "sub_67890",
  "request_type": "upgrade",
  "target_template_id": "tmpl_fiber_100",
  "effective_date": "2025-03-01",
  "notes": "Need higher speed for work from home"
}
```

**Response:**
```json
{
  "id": "req_77777",
  "subscription_id": "sub_67890",
  "request_type": "upgrade",
  "status": "pending_approval",
  "current_service": "Fiber 50Mbps",
  "requested_service": "Fiber 100Mbps",
  "price_difference": 10000,
  "effective_date": "2025-03-01",
  "estimated_processing_time": "2-3 business days"
}
```

---

## **🔄 Flow 5: Service Suspension & Restoration**

### **Automatic Suspension Due to Non-Payment**
```http
GET /api/v1/services/subscriptions/sub_67890
Authorization: Bearer {admin_jwt_token}
```

**Response (After Grace Period):**
```json
{
  "id": "sub_67890",
  "status": "suspended",
  "suspension": {
    "reason": "overdue_payment",
    "suspended_at": "2025-03-05T00:00:00Z",
    "days_suspended": 2,
    "restoration_fee": 2000,
    "outstanding_amount": 15000
  },
  "service_access": {
    "internet": false,
    "portal_access": true,
    "support_access": true
  }
}
```

### **Payment & Restoration**
```http
POST /api/v1/billing/payments/
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "customer_id": "cust_12345",
  "amount": 17000,
  "payment_method": "bank_transfer",
  "reference": "RESTORE_TXN_456",
  "notes": "Outstanding balance + restoration fee"
}
```

### **Automatic Service Restoration**
```http
POST /api/v1/services/subscriptions/sub_67890/restore
Authorization: Bearer {admin_jwt_token}
Content-Type: application/json

{
  "payment_id": "pay_88888",
  "restore_immediately": true
}
```

**Response:**
```json
{
  "id": "sub_67890",
  "status": "active",
  "restoration": {
    "restored_at": "2025-03-07T15:30:00Z",
    "restoration_fee_paid": 2000,
    "outstanding_cleared": true
  },
  "service_access": {
    "internet": true,
    "estimated_activation": "2025-03-07T15:35:00Z"
  }
}
```

---

## **📈 Flow 6: Monitoring & Analytics Journey**

### **Real-Time Service Monitoring**
```http
GET /api/v1/network/devices/router_lag_001/interfaces?customer_id=cust_12345
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "interfaces": [
    {
      "name": "ether5-customer-12345",
      "status": "up",
      "speed": "1Gbps",
      "customer_service": {
        "subscription_id": "sub_67890",
        "profile": "50M_25M",
        "current_usage": {
          "rx_rate": "12.5 Mbps",
          "tx_rate": "3.2 Mbps",
          "session_time": "02:15:30"
        }
      }
    }
  ]
}
```

### **Customer Usage Analytics**
```http
GET /api/v1/monitoring/dashboard/customer-analytics?customer_id=cust_12345&period=last_30_days
Authorization: Bearer {admin_jwt_token}
```

**Response:**
```json
{
  "analytics": {
    "usage_trends": {
      "average_daily_gb": 11.2,
      "peak_usage_day": "2025-02-15",
      "peak_usage_gb": 18.7,
      "usage_pattern": "evening_heavy"
    },
    "service_quality": {
      "uptime_percentage": 99.8,
      "average_speed_mbps": 47.3,
      "latency_avg_ms": 12,
      "packet_loss_percentage": 0.02
    },
    "support_metrics": {
      "tickets_created": 1,
      "avg_resolution_time": "4 hours",
      "satisfaction_score": 4.5
    }
  }
}
```

---

## **🎯 Postman Collection Structure**

### **Collection Organization**
```
ISP Framework API Flows/
├── 🚀 Customer Onboarding/
│   ├── 1. Create Customer
│   ├── 2. Browse Services  
│   ├── 3. Create Subscription
│   ├── 4. Provision Resources
│   ├── 5. Generate Invoice
│   ├── 6. Process Payment
│   └── 7. Check Service Status
├── 💳 Monthly Billing/
│   ├── 1. Get Customer Invoices
│   ├── 2. Process Payment
│   └── 3. Verify Payment
├── 🚨 Error Scenarios/
│   ├── Failed Payment
│   ├── Rate Limiting
│   └── Validation Errors
├── 👤 Customer Portal/
│   ├── Login & Dashboard
│   ├── View Usage
│   └── Request Upgrade
└── 🔄 Service Management/
    ├── Suspension Flow
    ├── Restoration Flow
    └── Monitoring & Analytics
```

### **Environment Variables**
```json
{
  "base_url": "http://localhost:8000/api/v1",
  "admin_token": "{{admin_jwt_token}}",
  "customer_token": "{{customer_jwt_token}}",
  "customer_id": "cust_12345",
  "subscription_id": "sub_67890",
  "invoice_id": "inv_22222"
}
```

---

## **📊 Visual Flow Diagrams**

### **Customer Onboarding Flow**
```
[Customer Request] 
    ↓
[POST /customers] → [Customer Created: cust_12345]
    ↓
[GET /services/templates] → [Available Plans Listed]
    ↓  
[POST /services/subscriptions] → [Subscription: sub_67890]
    ↓
[POST /services/provisioning] → [Resources Allocated]
    ↓
[POST /billing/invoices] → [Invoice: inv_22222]
    ↓
[POST /billing/payments] → [Payment: pay_33333]
    ↓
[GET /services/subscriptions/{id}] → [Service Active ✅]
```

### **Error Recovery Flow**
```
[Payment Attempt] 
    ↓
[Payment Fails ❌] → [Grace Period Started]
    ↓
[7 Days Later] → [Service Suspended ⚠️]
    ↓
[Customer Pays] → [Restoration Fee Applied]
    ↓
[POST /services/{id}/restore] → [Service Active ✅]
```

---

## **🎉 Summary**

These flow-based examples demonstrate:

✅ **Real-World Scenarios** - Complete customer journeys from signup to service delivery  
✅ **Data Continuity** - Same IDs used throughout each flow  
✅ **Error Handling** - Comprehensive error scenarios and recovery  
✅ **Self-Service** - Customer portal interactions  
✅ **Business Logic** - Suspension, restoration, and billing cycles  
✅ **Monitoring** - Real-time service analytics and quality metrics  

**Perfect for:**
- Developer onboarding
- API integration testing  
- Postman collection automation
- Customer support training
- Business process documentation
