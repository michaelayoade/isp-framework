# ISP Framework - Development Guidelines

## Overview
This document provides development guidelines and best practices derived from lessons learned during the Enhanced Authentication & Customer Management milestone implementation.

## Code Organization Standards

### Project Structure
The ISP Framework follows a modular architecture pattern:

```
app/
├── api/
│   ├── v1/
│   │   ├── endpoints/          # API route handlers
│   │   ├── dependencies.py     # Authentication dependencies
│   │   └── api.py             # Router registration
├── core/
│   ├── config.py              # Configuration management
│   ├── security.py            # Security utilities
│   ├── database.py            # Database connection
│   └── exceptions.py          # Custom exceptions
├── models/                    # SQLAlchemy models
├── schemas/                   # Pydantic schemas
├── services/                  # Business logic layer
├── repositories/              # Data access layer
└── main.py                   # Application entry point
```

### Module Naming Conventions
- **Models**: Singular nouns (e.g., `customer.py`, `service_plan.py`)
- **Services**: Descriptive names with "Service" suffix (e.g., `customer_service.py`)
- **Repositories**: Descriptive names with "Repository" suffix (e.g., `customer_repository.py`)
- **Schemas**: Match model names (e.g., `customer.py` for customer schemas)
- **Endpoints**: Plural nouns (e.g., `customers.py`, `service_plans.py`)

## Repository Pattern Implementation

### BaseRepository Usage
All data access MUST use the BaseRepository pattern:

```python
from app.repositories.base import BaseRepository
from app.models.customer import Customer

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = BaseRepository(Customer, db)
    
    def get_active_customers(self):
        return self.customer_repo.get_all(filters={"status": "active"})
    
    def count_customers_by_type(self, category: str):
        return self.customer_repo.count(filters={"category": category})
```

### Repository Method Standards
- Use `get_all(filters={})` for multiple records
- Use `count(filters={})` for counting with criteria
- Use `get_by_field(field, value)` for single record lookup
- Always handle SQLAlchemy exceptions in repository methods

## Service Layer Best Practices

### Service Method Structure
```python
def create_customer(self, customer_data: Dict[str, Any], admin_id: int) -> Customer:
    """Create a new customer with comprehensive data"""
    try:
        # 1. Input validation and transformation
        self._validate_customer_data(customer_data)
        
        # 2. Business logic processing
        if customer_data.get("password"):
            password = customer_data.pop("password")
            customer_data["password_hash"] = get_password_hash(password)
        
        # 3. Default value assignment
        customer_data.setdefault("status", "new")
        
        # 4. Database operation
        customer = self.customer_repo.create(customer_data)
        
        # 5. Post-creation tasks
        self._create_default_billing_config(customer.id)
        
        # 6. Logging and return
        logger.info(f"Customer created: {customer.login} (ID: {customer.id})")
        return customer
        
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise
```

### Error Handling in Services
```python
try:
    # Service operation
    result = self.perform_operation()
    return result
except ValidationError as e:
    logger.warning(f"Validation error: {str(e)}")
    raise HTTPException(status_code=422, detail=str(e))
except NotFoundError as e:
    logger.info(f"Resource not found: {str(e)}")
    raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

## DateTime Handling Standards

### Timezone-Aware Operations
Always use timezone-aware datetime objects:

```python
from datetime import datetime, timezone

# ✅ Correct - timezone-aware
current_time = datetime.now(timezone.utc)
expiry_time = datetime.now(timezone.utc) + timedelta(hours=24)

# ❌ Incorrect - timezone-naive
current_time = datetime.utcnow()  # Will cause errors with DB models
```

### Database DateTime Fields
```python
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func

class Customer(Base):
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## Authentication Implementation

### Unified Authentication Dependency
```python
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Administrator:
    """Unified authentication supporting OAuth 2.0 and JWT"""
    token = credentials.credentials
    
    # Try OAuth first
    try:
        oauth_token = oauth_service.validate_access_token(token)
        if oauth_token and oauth_token.user_id:
            admin = auth_service.admin_repo.get(oauth_token.user_id)
            if admin and admin.is_active:
                return admin
    except Exception:
        pass  # Fall through to JWT
    
    # Fallback to JWT
    try:
        admin = auth_service.get_current_admin(token)
        if admin:
            return admin
    except Exception:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

### Endpoint Protection
```python
@router.post("/", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Create customer with unified authentication"""
    service = CustomerService(db)
    return service.create_customer(customer_data.dict(), current_admin.id)
```

## Schema Design Patterns

### Pydantic Schema Structure
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class CustomerCreate(BaseModel):
    """Schema for creating customers"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr = Field(..., description="Customer email")
    password: Optional[str] = Field(None, min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class CustomerResponse(BaseModel):
    """Schema for customer responses"""
    id: int
    name: str
    email: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Schema Validation Best Practices
- Use descriptive field names and help text
- Implement custom validators for business rules
- Use appropriate field types (EmailStr, datetime, etc.)
- Set reasonable min/max lengths and values
- Use Optional for nullable fields

## API Endpoint Design

### RESTful Endpoint Structure
```python
@router.get("/", response_model=List[CustomerResponse])
async def list_customers():
    """List all customers"""

@router.post("/", response_model=CustomerResponse, status_code=201)
async def create_customer():
    """Create new customer"""

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    """Get customer by ID"""

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int):
    """Update customer"""

@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: int):
    """Delete customer"""
```

### Search and Filtering Endpoints
```python
@router.post("/search", response_model=CustomerSearchResponse)
async def search_customers(
    search_request: CustomerSearchRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(get_current_admin)
):
    """Search customers with filtering and pagination"""
    service = CustomerService(db)
    return service.search_customers(search_request.dict())
```

## Service Plan Development Guidelines

### Model and Repository Logic
- The `ServicePlan` repository MUST prevent the deletion of plans that are actively assigned to customers to maintain data integrity.
- The service layer MUST validate that only service plans with an `is_active` status can be assigned to a customer.

### Service Layer Responsibilities
- All business logic related to pricing, trials, or promotions MUST be implemented in the `ServicePlanService`.
- The service should handle all validation and error handling related to service plan management.

## Customer-Service Assignment Guidelines

### Association Object Pattern
- The `CustomerService` model acts as an association object and is critical for managing the many-to-many relationship between customers and service plans. It MUST contain all assignment-specific details like `status`, `start_date`, and `end_date`.

### Lifecycle Management
- The `CustomerServiceService` is responsible for managing the state transitions of a customer's service assignment (e.g., `pending` -> `active`, `active` -> `suspended`).
- All status changes MUST be logged for auditing purposes, including the timestamp and the administrator who performed the action.

### Data Integrity
- Relationships between `Customer`, `ServicePlan`, and `CustomerService` MUST use `back_populates` in SQLAlchemy to ensure that changes are synchronized across all related objects.
- The service layer MUST enforce logical constraints, such as ensuring an assignment's `end_date` is not before its `start_date`.

## Testing Guidelines

### Service Layer Testing
```python
import pytest
from unittest.mock import Mock, patch

class TestCustomerService:
    @pytest.fixture
    def customer_service(self, db_session):
        return CustomerService(db_session)
    
    def test_create_customer_success(self, customer_service):
        # Arrange
        customer_data = {
            "name": "Test Customer",
            "email": "test@example.com",
            "password": "testpass123"
        }
        
        # Act
        result = customer_service.create_customer(customer_data, admin_id=1)
        
        # Assert
        assert result.name == "Test Customer"
        assert result.email == "test@example.com"
        assert hasattr(result, 'password_hash')
        assert 'password' not in customer_data  # Removed after hashing
```

### API Endpoint Testing
```python
def test_create_customer_endpoint(client, auth_headers):
    # Arrange
    customer_data = {
        "name": "Test Customer",
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    # Act
    response = client.post(
        "/api/v1/customers/",
        json=customer_data,
        headers=auth_headers
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Customer"
    assert data["email"] == "test@example.com"
    assert "password" not in data
```

## Logging Standards

### Service-Level Logging
```python
import logging

logger = logging.getLogger(__name__)

class CustomerService:
    def create_customer(self, customer_data: Dict[str, Any], admin_id: int):
        logger.info(f"Creating customer: {customer_data.get('name')}")
        
        try:
            customer = self.customer_repo.create(customer_data)
            logger.info(f"Customer created successfully: {customer.login} (ID: {customer.id})")
            return customer
        except Exception as e:
            logger.error(f"Failed to create customer: {str(e)}", exc_info=True)
            raise
```

### Log Message Guidelines
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include relevant context (IDs, usernames, operation types)
- Avoid logging sensitive information (passwords, tokens)
- Use structured logging for better searchability
- Include exception details for error logs

## Performance Optimization

### Database Query Optimization
```python
# ✅ Good - Use database-level filtering
customers = self.customer_repo.get_all(
    filters={"status": "active", "category": "person"},
    limit=50,
    offset=0
)

# ❌ Bad - Application-level filtering
all_customers = self.customer_repo.get_all()
filtered = [c for c in all_customers if c.status == "active"]
```

### Pagination Implementation
```python
def search_customers(self, search_params: Dict[str, Any]):
    limit = min(search_params.get("limit", 50), 100)  # Cap at 100
    offset = max(search_params.get("offset", 0), 0)   # Ensure non-negative
    
    customers = self.customer_repo.get_all(
        filters=self._build_filters(search_params),
        limit=limit,
        offset=offset
    )
    
    total_count = self.customer_repo.count(
        filters=self._build_filters(search_params)
    )
    
    return {
        "customers": customers,
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }
```

## Security Best Practices

### Input Validation
```python
from pydantic import validator, Field

class CustomerCreate(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    phone: Optional[str] = Field(None, regex=r'^\+?[\d\s\-\(\)]+$')
    
    @validator('email')
    def validate_email_domain(cls, v):
        # Custom business rule validation
        if v.endswith('@blocked-domain.com'):
            raise ValueError('Email domain not allowed')
        return v
```

### Password Security
```python
from app.core.security import get_password_hash, verify_password

def create_customer(self, customer_data: Dict[str, Any]):
    if customer_data.get("password"):
        # Hash password and remove plain text
        password = customer_data.pop("password")
        customer_data["password_hash"] = get_password_hash(password)
        
        # Validate password strength
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
```

## Documentation Standards

### Code Documentation
```python
def create_customer(self, customer_data: Dict[str, Any], admin_id: int) -> Customer:
    """
    Create a new customer with comprehensive data validation and setup.
    
    Args:
        customer_data: Dictionary containing customer information
        admin_id: ID of the administrator creating the customer
        
    Returns:
        Customer: The created customer instance
        
    Raises:
        ValidationError: If customer data is invalid
        DuplicateError: If customer email already exists
        
    Example:
        >>> service = CustomerService(db)
        >>> customer_data = {"name": "John Doe", "email": "john@example.com"}
        >>> customer = service.create_customer(customer_data, admin_id=1)
    """
```

### API Documentation
```python
@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=201,
    summary="Create new customer",
    description="Create a new customer with comprehensive profile information",
    responses={
        201: {"description": "Customer created successfully"},
        400: {"description": "Invalid customer data"},
        409: {"description": "Customer email already exists"},
        422: {"description": "Validation error"}
    }
)
async def create_customer():
    """Create a new customer account"""
```

## Deployment Guidelines

### Environment Configuration
```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    oauth_client_secret: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Health Check Implementation
```python
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Application health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")
```

---

**Last Updated:** 2025-07-23  
**Version:** 1.0  
**Status:** Active  
**Based On:** Enhanced Authentication & Customer Management Milestone Implementation
