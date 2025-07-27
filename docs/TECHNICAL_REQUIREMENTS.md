# ISP Framework - Technical Requirements

## Overview
This document outlines the technical requirements and standards for the ISP Framework based on lessons learned from the Enhanced Authentication & Customer Management milestone.

## Repository Pattern Guidelines

### BaseRepository Usage Standards
All services MUST adhere to the following repository patterns:

#### ✅ Correct Usage
```python
# Get multiple records with filtering
customers = self.customer_repo.get_all(filters={"status": "active"})

# Count records with filtering  
count = self.customer_repo.count(filters={"category": "person"})

# Get single record by field
customer = self.customer_repo.get_by_field("email", "user@example.com")
```

#### ❌ Incorrect Usage
```python
# These methods DO NOT exist in BaseRepository
customers = self.customer_repo.get_all_by_field("status", "active")  # ERROR
count = self.customer_repo.count_by_field("category", "person")      # ERROR
```

### Custom Repository Methods
- Custom repository methods MUST be documented and tested
- Filter parameters MUST use dictionary format: `filters={"field": "value"}`
- All repository methods MUST handle SQLAlchemy exceptions properly
- Repository methods MUST include appropriate logging

## DateTime Handling Standards

### Timezone-Aware DateTime Requirements
All datetime operations MUST use timezone-aware objects to prevent database/model errors.

#### ✅ Correct Usage
```python
from datetime import datetime, timezone

# For current time operations
current_time = datetime.now(timezone.utc)

# For date calculations
account_age = (datetime.now(timezone.utc) - customer.created_at).days
```

#### ❌ Incorrect Usage
```python
# This creates timezone-naive objects causing errors
current_time = datetime.utcnow()  # ERROR
```

### Database DateTime Fields
- All datetime fields in database models MUST include timezone information
- SQLAlchemy datetime columns MUST use `DateTime(timezone=True)`
- Default values MUST use `server_default=func.now()`

## Authentication Integration Requirements

### Unified Authentication System
All endpoints MUST support unified OAuth 2.0 + JWT authentication:

#### Authentication Dependencies
```python
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Administrator:
    """
    Unified authentication supporting both OAuth and JWT tokens
    """
    # Try OAuth token validation first
    # Fallback to JWT token validation
    # Return authenticated admin or raise HTTPException
```

### Authentication Standards
- Token validation MUST be handled at dependency level
- Authentication failures MUST return consistent error formats
- All protected endpoints MUST use the unified authentication dependency
- Token expiration MUST be handled gracefully with appropriate error messages

## Password Field Handling

### Schema to Model Transformation
Password fields in schemas MUST be properly transformed before model instantiation:

#### ✅ Correct Implementation
```python
def create_customer(self, customer_data: Dict[str, Any], admin_id: int):
    # Hash password if provided and remove original password field
    if customer_data.get("password"):
        password = customer_data.pop("password")  # Remove from data
        customer_data["password_hash"] = get_password_hash(password)
    
    # Now safe to create model instance
    customer = self.customer_repo.create(customer_data)
```

#### ❌ Incorrect Implementation
```python
# This will cause model constructor errors
if customer_data.get("password"):
    customer_data["password_hash"] = get_password_hash(customer_data["password"])
    # password field still in data - ERROR when creating model
```

## Error Handling Standards

### Exception Management
- All service methods MUST handle exceptions appropriately
- Database exceptions MUST be caught and logged
- User-friendly error messages MUST be returned to clients
- Internal errors MUST be logged with full stack traces

### HTTP Status Codes
- `200 OK` - Successful operations
- `201 Created` - Successful resource creation
- `400 Bad Request` - Client validation errors
- `401 Unauthorized` - Authentication failures
- `403 Forbidden` - Authorization failures
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Schema validation errors
- `500 Internal Server Error` - Server errors

## Logging Standards

### Service-Level Logging
All services MUST implement comprehensive logging:

```python
import logging
logger = logging.getLogger(__name__)

# Info level for successful operations
logger.info(f"Customer created: {customer.login} (ID: {customer.id})")

# Warning level for recoverable issues
logger.warning(f"Invalid client secret for client: {client_id}")

# Error level for exceptions
logger.error(f"Error creating customer: {str(e)}")
```

### Log Message Format
- Include relevant identifiers (IDs, usernames, etc.)
- Use consistent formatting across services
- Include operation context and outcomes
- Avoid logging sensitive information (passwords, tokens)

## Testing Requirements

### Comprehensive Testing Strategy
- Unit tests for all service methods
- Integration tests for API endpoints
- End-to-end testing with curl or automated tools
- Error scenario testing for all failure modes

### Test Data Management
- Use consistent test data across test suites
- Clean up test data after test execution
- Use database transactions for test isolation
- Mock external dependencies appropriately

## Performance Standards

### Database Query Optimization
- Use appropriate indexes for frequently queried fields
- Implement pagination for large result sets
- Use database-level filtering instead of application filtering
- Monitor and optimize slow queries

### API Response Times
- Customer CRUD operations: < 200ms
- Search operations: < 500ms
- Complex reporting: < 2000ms
- Authentication operations: < 100ms

## Security Requirements

### Data Protection
- All passwords MUST be hashed using bcrypt or similar
- Sensitive data MUST NOT be logged
- Database connections MUST use encrypted connections
- API keys and secrets MUST be stored securely

### Input Validation
- All user inputs MUST be validated using Pydantic schemas
- SQL injection prevention through parameterized queries
- XSS prevention through proper output encoding
- Rate limiting on authentication endpoints

## Documentation Standards

### Code Documentation
- All public methods MUST have docstrings
- Complex business logic MUST be commented
- API endpoints MUST have comprehensive OpenAPI documentation
- Database schema changes MUST be documented

### API Documentation
- All endpoints MUST include request/response examples
- Error responses MUST be documented
- Authentication requirements MUST be clearly specified
- Rate limiting and usage guidelines MUST be provided

## SQLAlchemy Relationship Management

### Bidirectional Relationships
- All bidirectional relationships MUST use `back_populates` to ensure proper synchronization between models.
- Foreign key relationships MUST be clearly defined and documented.

```python
# CORRECT - Use back_populates for bidirectional relationships
class Customer(Base):
    services = relationship("CustomerService", back_populates="customer")

class CustomerService(Base):
    customer = relationship("Customer", back_populates="services")
```

## Pydantic Schema Serialization

### SQLAlchemy Model Serialization
- Pydantic schemas used for response models MUST include `from_attributes = True` in their `Config` class to properly serialize SQLAlchemy model objects.

```python
# CORRECT - Use from_attributes for SQLAlchemy model serialization
class BasicCustomerResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True
```

## Service Plan Technical Requirements

### Model & Schema Design
- Service plan models MUST include fields for `name`, `description`, `price`, `service_type`, `is_active`, and any service-specific attributes (e.g., data caps, speed limits).
- Pydantic schemas MUST be used for request validation and response serialization, ensuring proper data types and constraints.

### Repository & Service Logic
- The repository layer MUST prevent the deletion of any `ServicePlan` that has active `CustomerService` assignments.
- The service layer MUST validate that only `active` service plans can be assigned to customers.
- Business logic for promotional pricing or trial periods MUST be handled within the service layer.

## Customer-Service Assignment Technical Requirements

### Association Object Pattern
- The `CustomerService` model MUST be used as an association object to manage the many-to-many relationship between `Customer` and `ServicePlan`.
- This model MUST contain assignment-specific attributes such as `status`, `start_date`, `end_date`, and `activation_date`.

### Relationship & Data Integrity
- SQLAlchemy relationships between `Customer`, `CustomerService`, and `ServicePlan` MUST be correctly configured with `back_populates` to ensure data consistency.
- The service layer MUST enforce logical constraints, such as ensuring `end_date` is after `start_date`.

### Lifecycle Management
- The service layer is responsible for managing the state transitions of a service assignment (e.g., from `pending` to `active`).
- All status changes MUST be logged with a timestamp and the responsible administrator's ID for auditing purposes.

## Business Logic Validation

- All business logic (e.g., duplicate checks, status transitions) MUST be implemented in the service layer.
- The service layer MUST return appropriate exceptions for validation failures.
- All validation rules MUST be documented in the API contract.

---

**Last Updated:** 2025-07-23  
**Version:** 1.1  
**Status:** Active
