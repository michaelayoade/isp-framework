# Contributing to ISP Framework

Welcome to the ISP Framework! We're excited to have you contribute to building the most comprehensive open-source ISP management platform. This guide will help you get started with development, code standards, and contribution workflows.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**
- **Node.js 18+** (for frontend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ispframework/isp-framework.git
   cd isp-framework
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

3. **Start development environment**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Check service health
   docker-compose ps
   ```

4. **Verify installation**
   ```bash
   # API health check
   curl http://localhost:8000/health
   
   # Access Swagger UI
   open http://localhost:8000/docs
   ```

## 📋 Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: New features (`feature/customer-portal`)
- **bugfix/**: Bug fixes (`bugfix/billing-calculation`)
- **hotfix/**: Critical production fixes

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(billing): add automated invoice generation
fix(auth): resolve JWT token expiration issue
docs(api): update customer endpoint documentation
test(services): add unit tests for service provisioning
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes with tests**
   ```bash
   # Write code
   # Add tests
   # Update documentation
   ```

3. **Run quality checks**
   ```bash
   # Format code
   make format
   
   # Run linting
   make lint
   
   # Run tests
   make test
   
   # Type checking
   make typecheck
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat(billing): add automated invoice generation"
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use the PR template
   - Link related issues
   - Add screenshots for UI changes
   - Request reviews from maintainers

## 🎨 Code Style & Standards

### Python Code Style

We use **Black**, **Ruff**, and **MyPy** for code quality:

#### Black (Code Formatting)
```bash
# Format all Python files
black .

# Check formatting
black --check .
```

#### Ruff (Linting)
```bash
# Lint all files
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

#### MyPy (Type Checking)
```bash
# Type check
mypy app/

# Type check with strict mode
mypy --strict app/
```

### Configuration Files

**pyproject.toml**:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "C90", "I", "N", "UP", "B", "A", "C4", "T20"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### Code Quality Standards

#### Function Documentation
```python
def create_customer(
    name: str,
    email: str,
    phone: Optional[str] = None
) -> Customer:
    """
    Create a new customer account.
    
    Args:
        name: Customer full name
        email: Valid email address
        phone: Optional phone number
        
    Returns:
        Created customer instance
        
    Raises:
        ValidationError: If email format is invalid
        DuplicateError: If customer already exists
        
    Example:
        >>> customer = create_customer("John Doe", "john@example.com")
        >>> print(customer.id)
        123
    """
    # Implementation here
```

#### Error Handling
```python
from app.core.exceptions import ISPFrameworkException

class CustomerNotFoundError(ISPFrameworkException):
    """Raised when customer cannot be found."""
    
    def __init__(self, customer_id: int):
        super().__init__(
            message=f"Customer {customer_id} not found",
            error_code="CUSTOMER_NOT_FOUND",
            status_code=404
        )
```

#### Database Models
```python
from app.core.audit_mixins import EnhancedAuditMixin

class Customer(Base, EnhancedAuditMixin):
    """Customer account model."""
    
    __tablename__ = "customers"
    __audit_enabled__ = True  # Enable audit tracking
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, email='{self.email}')>"
```

## 🧪 Testing Standards

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
├── fixtures/      # Test fixtures
└── conftest.py    # Pytest configuration
```

### Writing Tests

#### Unit Tests
```python
import pytest
from app.services.customer_service import CustomerService
from app.models.customer import Customer

class TestCustomerService:
    """Test suite for CustomerService."""
    
    def test_create_customer_success(self, db_session):
        """Test successful customer creation."""
        service = CustomerService(db_session)
        
        customer = service.create_customer(
            name="John Doe",
            email="john@example.com"
        )
        
        assert customer.id is not None
        assert customer.name == "John Doe"
        assert customer.email == "john@example.com"
    
    def test_create_customer_duplicate_email(self, db_session):
        """Test customer creation with duplicate email."""
        service = CustomerService(db_session)
        
        # Create first customer
        service.create_customer("John Doe", "john@example.com")
        
        # Attempt to create duplicate
        with pytest.raises(DuplicateError):
            service.create_customer("Jane Doe", "john@example.com")
```

#### Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestCustomerAPI:
    """Integration tests for customer API."""
    
    def test_create_customer_endpoint(self, client: TestClient, auth_headers):
        """Test customer creation endpoint."""
        response = client.post(
            "/api/v1/customers",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_customer_service.py

# Run tests with specific marker
pytest -m "unit"

# Run tests in parallel
pytest -n auto
```

## 🔧 Development Tools

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### Makefile Commands

```makefile
.PHONY: help format lint test typecheck install dev

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:  ## Start development environment
	docker-compose up -d

format:  ## Format code with black
	black .
	ruff check --fix .

lint:  ## Run linting
	ruff check .
	mypy app/

test:  ## Run tests
	pytest --cov=app --cov-report=term-missing

typecheck:  ## Run type checking
	mypy app/

clean:  ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

docker-build:  ## Build Docker images
	docker-compose build

docker-test:  ## Run tests in Docker
	docker-compose run --rm backend pytest

migrate:  ## Run database migrations
	docker-compose exec backend alembic upgrade head

seed:  ## Seed database with test data
	docker-compose exec backend python scripts/seed_database.py
```

## 📚 Documentation Standards

### API Documentation

- **OpenAPI**: Auto-generated from FastAPI decorators
- **Docstrings**: Comprehensive function documentation
- **Examples**: Real-world usage examples
- **Error Codes**: Documented error responses

### Code Documentation

```python
class CustomerService:
    """
    Service layer for customer management operations.
    
    This service handles all business logic related to customer accounts,
    including creation, updates, billing integration, and service provisioning.
    
    Attributes:
        db: Database session
        audit_service: Audit logging service
        
    Example:
        >>> service = CustomerService(db_session)
        >>> customer = service.create_customer("John Doe", "john@example.com")
    """
    
    def __init__(self, db: Session, audit_service: AuditService):
        """Initialize customer service with dependencies."""
        self.db = db
        self.audit_service = audit_service
```

## 🚨 Security Guidelines

### Sensitive Data

- **Never commit secrets** to version control
- **Use environment variables** for configuration
- **Encrypt sensitive data** in database
- **Sanitize user inputs** to prevent injection

### Authentication

```python
from app.core.security import get_current_user

@router.post("/customers")
async def create_customer(
    customer_data: CustomerCreate,
    current_user: User = Depends(get_current_user)
):
    """Create customer with authentication required."""
    # Implementation here
```

### Input Validation

```python
from pydantic import BaseModel, validator, EmailStr

class CustomerCreate(BaseModel):
    """Customer creation schema with validation."""
    
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    
    @validator('name')
    def validate_name(cls, v):
        """Validate customer name."""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
```

## 🐛 Debugging & Troubleshooting

### Logging

```python
import logging
from app.core.logging import get_logger

logger = get_logger(__name__)

def process_payment(amount: Decimal):
    """Process payment with comprehensive logging."""
    logger.info("Processing payment", extra={
        "amount": str(amount),
        "currency": "USD"
    })
    
    try:
        # Payment processing logic
        result = payment_gateway.charge(amount)
        logger.info("Payment successful", extra={
            "transaction_id": result.id
        })
        return result
    except PaymentError as e:
        logger.error("Payment failed", extra={
            "error": str(e),
            "amount": str(amount)
        })
        raise
```

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### Migration Issues
```bash
# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Reset migrations (development only)
docker-compose exec backend alembic downgrade base
docker-compose exec backend alembic upgrade head
```

## 🎯 Performance Guidelines

### Database Optimization

```python
# Use eager loading for relationships
customers = db.query(Customer)\
    .options(joinedload(Customer.services))\
    .all()

# Use pagination for large datasets
def get_customers(page: int = 1, per_page: int = 50):
    return db.query(Customer)\
        .offset((page - 1) * per_page)\
        .limit(per_page)\
        .all()

# Use database indexes
class Customer(Base):
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, index=True)
```

### API Performance

```python
from fastapi import BackgroundTasks

@router.post("/customers/{id}/provision")
async def provision_service(
    customer_id: int,
    background_tasks: BackgroundTasks
):
    """Provision service asynchronously."""
    # Quick response
    background_tasks.add_task(provision_customer_service, customer_id)
    return {"status": "provisioning_started"}
```

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful** and inclusive
- **Help others** learn and grow
- **Give constructive feedback**
- **Follow project guidelines**

### Getting Help

1. **Check documentation** first
2. **Search existing issues** on GitHub
3. **Ask in Discord** for quick questions
4. **Create detailed issues** for bugs
5. **Propose RFCs** for major changes

### Recognition

Contributors are recognized through:
- **GitHub contributors** page
- **Release notes** mentions
- **Community highlights**
- **Maintainer nominations**

---

## 📞 Support

- **Documentation**: https://docs.ispframework.com
- **GitHub Issues**: https://github.com/ispframework/isp-framework/issues
- **Discord**: https://discord.gg/ispframework
- **Email**: contribute@ispframework.com

Thank you for contributing to ISP Framework! 🚀
