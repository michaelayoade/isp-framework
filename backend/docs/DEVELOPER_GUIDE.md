# ISP Framework Developer Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Architecture Overview](#architecture-overview)
3. [RBAC Implementation](#rbac-implementation)
4. [Service Layer Patterns](#service-layer-patterns)
5. [Testing Guidelines](#testing-guidelines)
6. [API Development](#api-development)
7. [Database Patterns](#database-patterns)
8. [Webhook Integration](#webhook-integration)
9. [Performance Optimization](#performance-optimization)
10. [Deployment Guide](#deployment-guide)

## Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose

### Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/ispframework/isp-framework.git
cd isp-framework
```

2. **Set up the backend environment:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your database and service configurations
```

4. **Run database migrations:**
```bash
alembic upgrade head
```

5. **Start the development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure

```
backend/
├── app/
│   ├── api/v1/                 # API endpoints
│   │   ├── endpoints/          # Individual endpoint modules
│   │   └── dependencies.py     # Shared dependencies
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database connection
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── rbac_decorators.py # RBAC decorators
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── services/               # Business logic layer
│   ├── repositories/           # Data access layer
│   └── utils/                  # Utility functions
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── docs/                       # Documentation
└── requirements.txt            # Python dependencies
```

## Architecture Overview

### Layered Architecture

The ISP Framework follows a clean layered architecture:

```
┌─────────────────┐
│   API Layer     │  ← FastAPI endpoints, request/response handling
├─────────────────┤
│  Service Layer  │  ← Business logic, orchestration
├─────────────────┤
│Repository Layer │  ← Data access, database queries
├─────────────────┤
│   Model Layer   │  ← SQLAlchemy models, database schema
└─────────────────┘
```

### Key Principles

1. **Separation of Concerns**: Each layer has a specific responsibility
2. **Dependency Injection**: Services are injected through FastAPI dependencies
3. **RBAC Integration**: Role-based access control at every layer
4. **Event-Driven**: Webhook triggers for system events
5. **Async Processing**: Background jobs for long-running operations

## RBAC Implementation

### Permission System

The RBAC system uses enum-based permissions for type safety:

```python
from app.services.rbac_service import Permission, ResourceType
from app.core.rbac_decorators import require_permission

@require_permission(Permission.CUSTOMER_CREATE)
async def create_customer(
    customer_data: CustomerCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Implementation
    pass
```

### Row-Level Security

Implement ownership-based access control:

```python
from app.core.rbac_decorators import require_ownership

@require_ownership(ResourceType.CUSTOMER, "customer_id")
async def get_customer(
    customer_id: int,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Only returns customer if user has access
    pass
```

### Query Filtering

Automatically filter queries based on user permissions:

```python
from app.core.rbac_decorators import filter_by_ownership

@filter_by_ownership(ResourceType.CUSTOMER)
async def list_customers(
    rbac_service: RBACService = Depends(get_rbac_service),
    current_admin: Administrator = Depends(get_current_admin)
):
    query = db.query(Customer)
    filtered_query = rbac_service.filter_query_by_ownership(
        query, current_admin, ResourceType.CUSTOMER
    )
    return filtered_query.all()
```

### Custom Permissions

Define custom permissions for specific use cases:

```python
class CustomPermission(str, Enum):
    BULK_CUSTOMER_IMPORT = "bulk_customer:import"
    ADVANCED_REPORTING = "reporting:advanced"

# Add to role permissions mapping
role_permissions = {
    UserRole.ADMIN: [
        Permission.CUSTOMER_CREATE,
        CustomPermission.BULK_CUSTOMER_IMPORT
    ]
}
```

## Service Layer Patterns

### Service Base Class

Create a base service class for common functionality:

```python
from sqlalchemy.orm import Session
from app.services.webhook_integration_service import WebhookTriggers

class BaseService:
    def __init__(self, db: Session):
        self.db = db
        self.webhook_triggers = WebhookTriggers(db)
    
    def _trigger_event(self, event_type: str, data: dict):
        """Trigger webhook event."""
        getattr(self.webhook_triggers, event_type)(data)
    
    def _validate_required_fields(self, data: dict, required_fields: list):
        """Validate required fields in data."""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
```

### Service Implementation Example

```python
from app.services.base_service import BaseService
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate

class CustomerService(BaseService):
    def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Create a new customer with validation and event triggers."""
        try:
            # Validate required fields
            self._validate_required_fields(
                customer_data.dict(), 
                ['name', 'email', 'phone']
            )
            
            # Check for duplicates
            existing = self.db.query(Customer).filter(
                Customer.email == customer_data.email
            ).first()
            
            if existing:
                raise ValidationError("Customer with this email already exists")
            
            # Create customer
            customer = Customer(**customer_data.dict())
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
            
            # Trigger webhook
            self._trigger_event('customer_created', {
                'customer_id': customer.id,
                'name': customer.name,
                'email': customer.email
            })
            
            return customer
            
        except Exception as e:
            self.db.rollback()
            raise
```

### Error Handling Pattern

Implement consistent error handling across services:

```python
import logging
from app.core.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)

class ServiceWithErrorHandling(BaseService):
    def risky_operation(self, data: dict):
        try:
            # Business logic here
            result = self._perform_operation(data)
            return result
            
        except ValidationError as e:
            # Re-raise validation errors
            logger.warning(f"Validation error in {self.__class__.__name__}: {e}")
            raise
            
        except Exception as e:
            # Log and wrap unexpected errors
            logger.error(f"Unexpected error in {self.__class__.__name__}: {e}")
            raise ServiceError(f"Operation failed: {str(e)}")
```

## Testing Guidelines

### Test Structure

Organize tests to mirror the application structure:

```
tests/
├── api/
│   ├── test_customer_endpoints.py
│   └── test_service_endpoints.py
├── services/
│   ├── test_customer_service.py
│   └── test_rbac_service.py
├── models/
│   └── test_customer_model.py
└── conftest.py  # Shared fixtures
```

### Service Testing Pattern

```python
import pytest
from unittest.mock import Mock, patch
from app.services.customer_service import CustomerService

class TestCustomerService:
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def customer_service(self, mock_db):
        return CustomerService(mock_db)
    
    @pytest.fixture
    def sample_customer_data(self):
        return {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890'
        }
    
    def test_create_customer_success(self, customer_service, sample_customer_data):
        # Arrange
        with patch.object(customer_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = None
            
            # Act
            result = customer_service.create_customer(sample_customer_data)
            
            # Assert
            assert result.name == sample_customer_data['name']
            customer_service.db.add.assert_called_once()
            customer_service.db.commit.assert_called_once()
    
    def test_create_customer_duplicate_email(self, customer_service, sample_customer_data):
        # Arrange
        existing_customer = Mock()
        with patch.object(customer_service.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = existing_customer
            
            # Act & Assert
            with pytest.raises(ValidationError):
                customer_service.create_customer(sample_customer_data)
```

### API Endpoint Testing

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_customer_endpoint():
    # Test data
    customer_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890'
    }
    
    # Make request
    response = client.post('/customers', json=customer_data)
    
    # Assert response
    assert response.status_code == 201
    assert response.json()['name'] == customer_data['name']
    assert 'id' in response.json()
```

### Mock External Services

```python
@patch('app.services.payment_service.PaymentGateway')
def test_process_payment(mock_payment_gateway, payment_service):
    # Arrange
    mock_gateway_instance = Mock()
    mock_payment_gateway.return_value = mock_gateway_instance
    mock_gateway_instance.charge.return_value = {'status': 'success', 'transaction_id': '123'}
    
    # Act
    result = payment_service.process_payment(100.00, 'card_token')
    
    # Assert
    assert result['status'] == 'success'
    mock_gateway_instance.charge.assert_called_once_with(100.00, 'card_token')
```

## API Development

### Endpoint Pattern

Follow this pattern for consistent API endpoints:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.dependencies import get_current_admin
from app.core.rbac_decorators import require_permission

router = APIRouter()

@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
@require_permission(Permission.CUSTOMER_CREATE)
async def create_customer(
    customer_data: CustomerCreate,
    current_admin: Administrator = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new customer.
    
    - **name**: Customer full name
    - **email**: Customer email address (must be unique)
    - **phone**: Customer phone number
    """
    try:
        customer_service = CustomerService(db)
        customer = customer_service.create_customer(customer_data)
        return customer
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Request/Response Schemas

Define clear Pydantic schemas:

```python
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        # Phone validation logic
        if not v.startswith('+'):
            raise ValueError('Phone must include country code')
        return v

class CustomerCreate(CustomerBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class CustomerResponse(CustomerBase):
    id: int
    portal_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

### Pagination Pattern

Implement consistent pagination:

```python
from app.schemas.common import PaginatedResponse

@router.get("/customers", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    customer_service = CustomerService(db)
    customers, total = customer_service.list_customers(
        page=page, 
        per_page=per_page, 
        search=search
    )
    
    return PaginatedResponse(
        items=customers,
        total=total,
        page=page,
        per_page=per_page,
        pages=((total - 1) // per_page) + 1 if total > 0 else 0
    )
```

## Database Patterns

### Model Definition

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=False)
    portal_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="active", index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    services = relationship("Service", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}')>"
```

### Repository Pattern

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer

class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, customer_data: dict) -> Customer:
        customer = Customer(**customer_data)
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
    
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.id == customer_id).first()
    
    def get_by_email(self, email: str) -> Optional[Customer]:
        return self.db.query(Customer).filter(Customer.email == email).first()
    
    def list_with_pagination(self, page: int, per_page: int, search: Optional[str] = None):
        query = self.db.query(Customer)
        
        if search:
            query = query.filter(
                Customer.name.ilike(f"%{search}%") |
                Customer.email.ilike(f"%{search}%")
            )
        
        total = query.count()
        customers = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return customers, total
    
    def update(self, customer_id: int, update_data: dict) -> Optional[Customer]:
        customer = self.get_by_id(customer_id)
        if customer:
            for key, value in update_data.items():
                setattr(customer, key, value)
            self.db.commit()
            self.db.refresh(customer)
        return customer
    
    def delete(self, customer_id: int) -> bool:
        customer = self.get_by_id(customer_id)
        if customer:
            self.db.delete(customer)
            self.db.commit()
            return True
        return False
```

### Migration Best Practices

```python
"""Add customer portal_id field

Revision ID: abc123
Revises: def456
Create Date: 2025-01-29 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    # Add column with nullable=True first
    op.add_column('customers', sa.Column('portal_id', sa.String(), nullable=True))
    
    # Populate existing records
    op.execute("""
        UPDATE customers 
        SET portal_id = '1000' || LPAD(id::text, 4, '0')
        WHERE portal_id IS NULL
    """)
    
    # Make column non-nullable and add unique constraint
    op.alter_column('customers', 'portal_id', nullable=False)
    op.create_unique_constraint('uq_customers_portal_id', 'customers', ['portal_id'])
    op.create_index('ix_customers_portal_id', 'customers', ['portal_id'])

def downgrade():
    op.drop_index('ix_customers_portal_id', 'customers')
    op.drop_constraint('uq_customers_portal_id', 'customers', type_='unique')
    op.drop_column('customers', 'portal_id')
```

## Webhook Integration

### Event Definition

```python
from enum import Enum

class WebhookEvent(str, Enum):
    CUSTOMER_CREATED = "customer.created"
    SERVICE_ACTIVATED = "service.activated"
    PAYMENT_RECEIVED = "payment.received"
    SLA_BREACHED = "sla.breached"

class WebhookTriggers:
    def __init__(self, db: Session):
        self.db = db
    
    def customer_created(self, data: dict):
        self._send_webhook(WebhookEvent.CUSTOMER_CREATED, data)
    
    def _send_webhook(self, event: WebhookEvent, data: dict):
        payload = {
            'event': event,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data': data
        }
        
        # Queue webhook for delivery
        self._queue_webhook_delivery(payload)
```

### Webhook Security

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature using HMAC-SHA256."""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

## Performance Optimization

### Database Query Optimization

```python
# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload

customers = db.query(Customer)\
    .options(joinedload(Customer.services))\
    .filter(Customer.status == 'active')\
    .all()

# Use pagination for large datasets
def get_customers_paginated(db: Session, page: int, per_page: int):
    return db.query(Customer)\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()
```

### Caching Strategy

```python
from functools import lru_cache
import redis

# In-memory caching for small, frequently accessed data
@lru_cache(maxsize=128)
def get_service_plans():
    return db.query(ServicePlan).all()

# Redis caching for larger datasets
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_customer_with_cache(customer_id: int):
    cache_key = f"customer:{customer_id}"
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        redis_client.setex(cache_key, 300, json.dumps(customer.dict()))
    
    return customer
```

### Background Jobs

```python
from celery import Celery

celery_app = Celery('isp_framework')

@celery_app.task
def process_service_provisioning(service_id: int):
    """Background task for service provisioning."""
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if service:
            # Perform provisioning logic
            provision_service(service)
            service.status = 'active'
            db.commit()
    except Exception as e:
        logger.error(f"Provisioning failed for service {service_id}: {e}")
        raise
```

## Deployment Guide

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ispframework
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: ispframework
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **Database**: Use connection pooling and read replicas
3. **Monitoring**: Implement logging, metrics, and alerting
4. **Security**: Enable HTTPS, rate limiting, and input validation
5. **Scaling**: Use load balancers and horizontal scaling

### Health Checks

```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for load balancers."""
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        
        # Check Redis connectivity
        redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
```

## Best Practices Summary

1. **Code Organization**: Follow the layered architecture pattern
2. **Error Handling**: Use custom exceptions and consistent error responses
3. **Security**: Implement RBAC at every layer
4. **Testing**: Write comprehensive unit and integration tests
5. **Documentation**: Document all APIs and complex business logic
6. **Performance**: Use caching, pagination, and background jobs
7. **Monitoring**: Log important events and metrics
8. **Deployment**: Use containerization and infrastructure as code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

For more information, see our [Contributing Guidelines](CONTRIBUTING.md).
