# ISP Framework - API Contract Updates

## Overview
This document outlines necessary updates to the API contract based on lessons learned from the Enhanced Authentication & Customer Management milestone implementation.

## Schema Corrections Required

### 1. Repository Method Documentation

#### Current Issue
The API contract doesn't specify correct repository method usage patterns, leading to runtime errors.

#### Required Updates
Update all service layer documentation to reflect correct BaseRepository usage:

```yaml
# CORRECT - Use in all service implementations
get_all:
  parameters:
    filters: 
      type: object
      description: "Dictionary of field-value pairs for filtering"
      example: {"status": "active", "category": "person"}
    limit:
      type: integer
      minimum: 1
      maximum: 100
    offset:
      type: integer
      minimum: 0

count:
  parameters:
    filters:
      type: object
      description: "Dictionary of field-value pairs for filtering"
      example: {"status": "active"}
```

#### Remove Invalid Methods
Remove references to these non-existent methods from all documentation:
- `get_all_by_field(field, value)` ❌
- `count_by_field(field, value)` ❌

### 2. DateTime Field Specifications

#### Current Issue
Schema doesn't specify timezone-aware datetime requirements, causing runtime errors.

#### Required Updates
Update all datetime field definitions:

```yaml
datetime_fields:
  type: string
  format: date-time
  description: "ISO 8601 datetime with timezone information (UTC)"
  example: "2025-07-23T12:03:58+00:00"
  timezone_aware: true
  storage_format: "UTC"
  
# Update all model datetime fields
Customer:
  properties:
    created_at:
      type: string
      format: date-time
      timezone_aware: true
      description: "Customer creation timestamp (UTC)"
    updated_at:
      type: string
      format: date-time
      timezone_aware: true
      description: "Last update timestamp (UTC)"
```

### 3. Password Field Handling Documentation

#### Current Issue
Schema doesn't document password transformation process, causing model constructor errors.

#### Required Updates
Add clear documentation for password handling:

```yaml
CustomerCreate:
  properties:
    password:
      type: string
      format: password
      minLength: 8
      description: "Plain text password (will be hashed before storage)"
      transformation: "Converted to password_hash field using bcrypt"
      storage_note: "Original password field is removed after hashing"
      
CustomerResponse:
  properties:
    password_hash:
      type: string
      description: "Hashed password (bcrypt)"
      read_only: true
      exclude_from_response: true
```

## Authentication Integration Updates

### Unified Authentication Specification

#### Current Issue
API contract doesn't specify unified OAuth 2.0 + JWT authentication system.

#### Required Updates
Add comprehensive authentication documentation:

```yaml
security:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
    description: "Supports both OAuth 2.0 access tokens and JWT tokens"
    
authentication_flow:
  oauth2_flow:
    type: oauth2
    flows:
      clientCredentials:
        tokenUrl: /api/v1/auth/oauth/token
        scopes:
          admin: "Administrative access"
          read: "Read access"
          write: "Write access"
  
  jwt_fallback:
    type: http
    scheme: bearer
    description: "JWT token fallback for direct authentication"

unified_authentication:
  description: "All protected endpoints support both OAuth 2.0 and JWT tokens"
  validation_order:
    1: "OAuth 2.0 access token validation"
    2: "JWT token validation (fallback)"
  error_handling:
    401: "Invalid or expired token"
    403: "Insufficient permissions"
```

## Enhanced Customer Management Schema

### Customer Search Schema Updates

#### Current Implementation Validation
Based on successful testing, update search schema:

```yaml
CustomerSearchRequest:
  type: object
  properties:
    query:
      type: string
      description: "Text search across name, email, phone, login"
      example: "john@example.com"
    status:
      type: string
      enum: ["new", "active", "suspended", "terminated"]
      description: "Exact status filter"
    category:
      type: string
      enum: ["person", "company"]
      description: "Customer category filter"
    labels:
      type: array
      items:
        type: string
      description: "Filter by assigned labels"
      example: ["vip", "support"]
    location_id:
      type: integer
      description: "Filter by location"
    partner_id:
      type: integer
      description: "Filter by partner"
    limit:
      type: integer
      minimum: 1
      maximum: 100
      default: 50
      description: "Results per page"
    offset:
      type: integer
      minimum: 0
      default: 0
      description: "Pagination offset"

CustomerSearchResponse:
  type: object
  properties:
    customers:
      type: array
      items:
        $ref: "#/components/schemas/CustomerResponse"
    total_count:
      type: integer
      description: "Total matching records"
    limit:
      type: integer
      description: "Applied limit"
    offset:
      type: integer
      description: "Applied offset"
  required: [customers, total_count, limit, offset]
```

### Customer Labels Schema Updates

#### Validated Implementation
Update label schema based on successful testing:

```yaml
CustomerLabelCreate:
  type: object
  properties:
    customer_id:
      type: integer
      description: "Customer ID"
    label_id:
      type: integer
      description: "Label ID"
    notes:
      type: string
      description: "Assignment notes/reason"
      maxLength: 1000
    assigned_by:
      type: integer
      description: "Admin ID (auto-populated from auth)"
      read_only: true
  required: [customer_id, label_id]

CustomerLabelResponse:
  type: object
  properties:
    id:
      type: integer
    customer_id:
      type: integer
    label_id:
      type: integer
    label:
      $ref: "#/components/schemas/LabelResponse"
    notes:
      type: string
    assigned_by:
      type: integer
    assigned_at:
      type: string
      format: date-time
      timezone_aware: true
```

### Customer Notes Schema Updates

#### Validated Implementation
Update notes schema based on successful testing:

```yaml
CustomerNoteCreate:
  type: object
  properties:
    customer_id:
      type: integer
      description: "Customer ID"
    note_type:
      type: string
      enum: ["general", "onboarding", "support", "billing"]
      default: "general"
    priority:
      type: string
      enum: ["low", "normal", "high", "urgent"]
      default: "normal"
    is_internal:
      type: boolean
      default: true
      description: "Internal note (not visible to customer)"
    content:
      type: string
      description: "Note content"
      maxLength: 5000
  required: [customer_id, content]

CustomerNoteResponse:
  type: object
  properties:
    id:
      type: integer
    customer_id:
      type: integer
    note_type:
      type: string
    priority:
      type: string
    is_internal:
      type: boolean
    content:
      type: string
    created_by:
      type: integer
    created_at:
      type: string
      format: date-time
      timezone_aware: true
```

### Customer Documents Schema Updates

#### Validated Implementation
Update documents schema based on successful testing:

```yaml
CustomerDocumentCreate:
  type: object
  properties:
    customer_id:
      type: integer
      description: "Customer ID"
    document_type:
      type: string
      enum: ["ID_CARD", "PROOF_OF_ADDRESS", "BUSINESS_REGISTRATION", "TAX_CERTIFICATE", "BANK_DETAILS", "CONTRACT", "INVOICE"]
    filename:
      type: string
      description: "Original filename"
      maxLength: 255
    file_size:
      type: integer
      description: "File size in bytes"
    mime_type:
      type: string
      description: "MIME type"
      example: "application/pdf"
    storage_path:
      type: string
      description: "Internal storage path"
    expiry_date:
      type: string
      format: date
      description: "Document expiry date (optional)"
    is_verified:
      type: boolean
      default: false
      description: "Document verification status"
  required: [customer_id, document_type, filename, file_size, mime_type, storage_path]
```

### Customer Billing Configuration Updates

#### Validated Implementation
Update billing config schema based on successful testing:

```yaml
CustomerBillingConfigUpdate:
  type: object
  properties:
    billing_cycle:
      type: string
      enum: ["monthly", "quarterly", "semi-annually", "annually", "custom"]
      default: "monthly"
    billing_day:
      type: integer
      minimum: 1
      maximum: 28
      default: 1
      description: "Day of month for billing"
    payment_terms:
      type: integer
      default: 30
      description: "Payment terms in days"
    late_fee_percentage:
      type: number
      format: decimal
      minimum: 0
      maximum: 100
      default: 5.0
    credit_limit:
      type: number
      format: decimal
      minimum: 0
      description: "Credit limit amount"
    auto_suspend_on_overdue:
      type: boolean
      default: false
    discount_percentage:
      type: number
      format: decimal
      minimum: 0
      maximum: 100
      default: 0
    tax_exempt:
      type: boolean
      default: false
    preferred_payment_method:
      type: string
      enum: ["credit_card", "bank_transfer", "check", "cash"]
```

## Error Response Schema Updates

### Standardized Error Format

#### Current Issue
Inconsistent error response formats across endpoints.

#### Required Updates
Standardize all error responses:

```yaml
ErrorResponse:
  type: object
  properties:
    detail:
      type: string
      description: "Human-readable error message"
    errors:
      type: array
      items:
        type: object
        properties:
          field:
            type: string
            description: "Field name causing error"
          message:
            type: string
            description: "Field-specific error message"
          code:
            type: string
            description: "Error code for programmatic handling"
        required: [field, message, code]
    timestamp:
      type: string
      format: date-time
      timezone_aware: true
      description: "Error timestamp"
    request_id:
      type: string
      description: "Unique request identifier for tracking"
  required: [detail, timestamp]

# Standard HTTP status codes with consistent error format
responses:
  400:
    description: "Bad Request"
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/ErrorResponse"
  401:
    description: "Unauthorized"
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/ErrorResponse"
  422:
    description: "Validation Error"
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/ErrorResponse"
```

## Performance and Pagination Updates

### Pagination Standards

#### Current Issue
Inconsistent pagination implementation across endpoints.

#### Required Updates
Standardize pagination for all list endpoints:

```yaml
PaginationRequest:
  type: object
  properties:
    limit:
      type: integer
      minimum: 1
      maximum: 100
      default: 50
      description: "Number of items per page"
    offset:
      type: integer
      minimum: 0
      default: 0
      description: "Number of items to skip"

PaginatedResponse:
  type: object
  properties:
    data:
      type: array
      description: "Array of result items"
    total_count:
      type: integer
      description: "Total number of items matching criteria"
    limit:
      type: integer
      description: "Applied limit"
    offset:
      type: integer
      description: "Applied offset"
    has_more:
      type: boolean
      description: "Whether more items are available"
  required: [data, total_count, limit, offset, has_more]
```

## Implementation Priority

### High Priority (Immediate)
1. ✅ Repository method documentation corrections
2. ✅ DateTime timezone-aware specifications
3. ✅ Password field handling documentation
4. ✅ Unified authentication specification

### Medium Priority (Next Sprint)
1. ✅ Enhanced customer management schemas
2. ✅ Standardized error response format
3. ✅ Pagination standards implementation

### Low Priority (Future Enhancement)
1. Advanced search capabilities
2. Bulk operation schemas
3. Webhook event specifications
4. API versioning strategy

## Customer-Service Assignment System

### New Endpoints Added

#### Search Customer Services
```yaml
GET /api/v1/customer-services/:
  summary: Search customer services with pagination and filtering
  parameters:
    - name: customer_id
      in: query
      type: integer
      description: Filter by customer ID
    - name: service_plan_id
      in: query
      type: integer
      description: Filter by service plan ID
    - name: status
      in: query
      type: string
      enum: [active, suspended, terminated, pending]
    - name: limit
      in: query
      type: integer
      default: 50
      maximum: 100
    - name: offset
      in: query
      type: integer
      default: 0
  responses:
    200:
      description: Customer services search results
      schema:
        $ref: '#/definitions/CustomerServiceSearchResponse'
```

#### Create Customer Service Assignment
```yaml
POST /api/v1/customer-services/:
  summary: Create new customer service assignment
  requestBody:
    required: true
    content:
      application/json:
        schema:
          $ref: '#/definitions/CustomerServiceCreate'
  responses:
    201:
      description: Customer service created successfully
      schema:
        $ref: '#/definitions/CustomerServiceResponse'
    400:
      description: Validation error or duplicate assignment
```

#### Status Management Endpoints
```yaml
PATCH /api/v1/customer-services/{service_id}/activate:
  summary: Activate customer service
PATCH /api/v1/customer-services/{service_id}/suspend:
  summary: Suspend customer service
PATCH /api/v1/customer-services/{service_id}/terminate:
  summary: Terminate customer service
```

### New Schema Definitions

#### CustomerServiceResponse
```yaml
CustomerServiceResponse:
  type: object
  properties:
    id: integer
    customer_id: integer
    service_plan_id: integer
    status: string (active, suspended, terminated, pending)
    custom_price: integer
    discount_percentage: integer
    effective_price: integer (calculated)
    monthly_cost: integer (calculated)
    service_plan: ServicePlan object
    customer: BasicCustomerResponse object
    created_at: datetime (timezone-aware)
    updated_at: datetime (timezone-aware)
```

## Service Plan Management Schema

### Validated Implementation
Update service plan schemas based on successful testing:

```yaml
ServicePlanCreate:
  type: object
  properties:
    name:
      type: string
      description: "Name of the service plan"
    price:
      type: number
      format: decimal
      description: "Price of the service plan"
    service_type:
      type: string
      enum: ["Internet", "Voice", "TV", "Bundle"]
      description: "Type of service"
  required: [name, price, service_type]

ServicePlanResponse:
  type: object
  properties:
    id:
      type: integer
    name:
      type: string
    price:
      type: number
    service_type:
      type: string
    is_active:
      type: boolean
```

## Customer-Service Assignment Schema

### Validated Implementation
Update customer-service assignment schemas based on successful testing:

```yaml
CustomerServiceCreate:
  type: object
  properties:
    customer_id:
      type: integer
      description: "ID of the customer"
    service_plan_id:
      type: integer
      description: "ID of the service plan to assign"
    start_date:
      type: string
      format: date-time
      description: "Service activation start date"
  required: [customer_id, service_plan_id, start_date]

CustomerServiceResponse:
  type: object
  properties:
    id:
      type: integer
    customer_id:
      type: integer
    service_plan_id:
      type: integer
    status:
      type: string
      enum: ["pending", "active", "suspended", "terminated"]
    start_date:
      type: string
      format: date-time
    end_date:
      type: string
      format: date-time
      nullable: true
    service_plan:
      $ref: "#/components/schemas/ServicePlanResponse"
```

---

**Last Updated:** 2025-07-23  
**Version:** 1.1  
**Status:** Active  
**Validation Status:** All updates based on successful milestone implementation and testing including Customer-Service Assignment system
