# Docker-Native Testing Guide

This guide covers the unified Docker-based testing strategy for the ISP Framework backend. All tests run inside Docker containers to ensure consistency and eliminate environment-specific issues.

## Overview

The ISP Framework uses a comprehensive Docker-native testing approach that provides:

- **Consistent Environment**: All tests run in the same Docker environment as production
- **Database Isolation**: Each test session uses a separate PostgreSQL schema
- **Parallel Execution**: Tests can run in parallel using pytest-xdist
- **Comprehensive Coverage**: Unit, integration, and API tests with coverage reporting
- **Infrastructure Mocking**: Redis, MinIO, and Ansible runner mocking for isolated testing

## Quick Start

### Running All Tests

```bash
# Basic test run
docker-compose exec backend pytest

# With coverage report
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# Parallel execution with coverage
docker-compose exec backend pytest -n auto --cov=app --cov-report=html
```

### Using the Test Runner Script

The project includes a comprehensive test runner script:

```bash
# Run all tests
./backend/scripts/run_tests.sh

# Run with coverage
./backend/scripts/run_tests.sh --coverage

# Run in parallel with coverage
./backend/scripts/run_tests.sh --parallel --coverage

# Run only unit tests
./backend/scripts/run_tests.sh --markers "unit"

# Skip integration tests
./backend/scripts/run_tests.sh --markers "not integration"

# Run specific feature tests
./backend/scripts/run_tests.sh --markers "rbac or device or automation"

# Clean artifacts and run with coverage
./backend/scripts/run_tests.sh --clean --coverage
```

## Test Organization

### Test Structure

```
tests/
├── conftest.py                 # Docker-native fixtures and configuration
├── test_device_management.py   # MAC authentication and device tests
├── test_automation_system.py   # Ansible automation tests
├── test_rbac_system.py         # Role-based access control tests
├── test_auth_flows.py          # Authentication flow tests
├── test_customer_service_repository.py  # Customer service tests
├── test_db_smoke.py            # Database smoke tests
├── test_observability.py       # Monitoring and observability tests
├── test_security.py            # Security feature tests
└── test_settings_management.py # Settings and configuration tests
```

### Test Markers

Tests are organized using pytest markers for selective execution:

#### Core Markers
- `unit`: Fast unit tests with no I/O dependencies
- `integration`: Integration tests requiring external services
- `api`: FastAPI endpoint tests requiring full app startup
- `db`: Tests that require database connection
- `slow`: Tests that take a long time to run

#### Feature-Specific Markers
- `rbac`: RBAC and permission tests
- `billing`: Billing system tests
- `network`: Network management tests
- `customer`: Customer management tests
- `auth`: Authentication and authorization tests
- `webhook`: Webhook integration tests
- `device`: Device management tests
- `automation`: Ansible automation tests

#### Infrastructure Markers
- `redis`: Tests requiring Redis
- `minio`: Tests requiring MinIO/S3 storage
- `radius`: Tests requiring FreeRADIUS
- `celery`: Tests requiring Celery workers

### Example Usage

```bash
# Run only unit tests
docker-compose exec backend pytest -m "unit"

# Run all tests except slow integration tests
docker-compose exec backend pytest -m "not integration and not slow"

# Run RBAC and device management tests
docker-compose exec backend pytest -m "rbac or device"

# Run all API tests with coverage
docker-compose exec backend pytest -m "api" --cov=app
```

## Test Configuration

### pytest.ini Configuration

The `pytest.ini` file is optimized for Docker container execution:

```ini
[tool:pytest]
# Docker-native test configuration for ISP Framework
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Optimized for Docker container execution
addopts = 
    -ra
    -q
    --tb=short
    --strict-markers
    --color=yes
    --disable-warnings
    --maxfail=10

# Environment variables for Docker testing
env =
    PYTHONPATH=/app
    LOG_LEVEL=WARNING
    TESTING=true
```

### Database Isolation

Each test session uses a separate PostgreSQL schema to ensure complete isolation:

- Schema naming: `pytest_{worker_id}` (e.g., `pytest_main`, `pytest_gw0`)
- Automatic schema creation and cleanup
- Full migration execution for each test session
- Transactional rollback for each test function

## Test Fixtures

### Core Fixtures

#### Database Fixtures
- `setup_test_database`: Session-scoped database schema management
- `db_session`: Function-scoped transactional database session
- `async_db_session`: Async version of database session

#### HTTP Client Fixtures
- `client`: Synchronous FastAPI TestClient
- `async_client`: Asynchronous HTTP client for async endpoints

#### Authentication Fixtures
- `super_admin`: Super administrator user for testing
- `regular_admin`: Regular administrator user for testing
- `auth_headers`: Authentication headers for API requests

#### Infrastructure Mocking Fixtures
- `mock_redis`: Mocked Redis client using fakeredis
- `mock_minio`: Mocked MinIO S3 client
- `mock_ansible_runner`: Mocked Ansible runner for automation tests

#### Sample Data Fixtures
- `sample_customer_data`: Sample customer data for testing
- `sample_device_data`: Sample device data for MAC authentication tests

### Example Fixture Usage

```python
@pytest.mark.device
def test_device_creation(db_session, sample_device_data):
    """Test device creation with sample data."""
    device_service = DeviceService(db_session)
    device = device_service.create_device(sample_device_data)
    assert device.mac_address == sample_device_data["mac_address"]

@pytest.mark.api
def test_device_api(client, auth_headers, sample_device_data):
    """Test device API endpoint."""
    response = client.post("/api/v1/devices", json=sample_device_data, headers=auth_headers)
    assert response.status_code == 201
```

## Coverage Reporting

### Generating Coverage Reports

```bash
# Terminal coverage report
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# HTML coverage report
docker-compose exec backend pytest --cov=app --cov-report=html:htmlcov

# XML coverage report (for CI)
docker-compose exec backend pytest --cov=app --cov-report=xml:coverage.xml

# Combined reports
docker-compose exec backend pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml
```

### Coverage Thresholds

The project maintains a minimum coverage threshold of 80%. CI pipelines will fail if coverage drops below this threshold.

```bash
# Check coverage threshold
docker-compose exec backend coverage report --fail-under=80
```

## Parallel Testing

### Using pytest-xdist

```bash
# Auto-detect CPU cores
docker-compose exec backend pytest -n auto

# Specify number of workers
docker-compose exec backend pytest -n 4

# Parallel with coverage (requires coverage[toml])
docker-compose exec backend pytest -n auto --cov=app --cov-report=term-missing
```

### Parallel Testing Considerations

- Database schemas are automatically isolated per worker
- Shared resources (Redis, MinIO) use mocking to avoid conflicts
- Some integration tests may need to be marked as `slow` to avoid resource contention

## Property-Based Testing

The project uses Hypothesis for property-based testing of critical business logic:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=100))
def test_customer_name_validation(name):
    """Property-based test for customer name validation."""
    # Test that any valid string can be used as a customer name
    assert validate_customer_name(name) is not None
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Start services
      run: docker-compose up -d postgres redis backend
    
    - name: Wait for services
      run: sleep 30
    
    - name: Run migrations
      run: docker-compose exec backend alembic upgrade head
    
    - name: Run tests with coverage
      run: docker-compose exec backend pytest --cov=app --cov-report=xml
    
    - name: Check coverage threshold
      run: |
        pct=$(docker-compose exec backend coverage report | awk '/TOTAL/ {print $4}' | sed 's/%//')
        test $(printf "%.0f" "$pct") -ge 80
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```

## Best Practices

### Test Writing Guidelines

1. **Use Descriptive Names**: Test function names should clearly describe what is being tested
2. **Follow AAA Pattern**: Arrange, Act, Assert structure for clear test organization
3. **Use Appropriate Markers**: Mark tests with relevant markers for selective execution
4. **Mock External Dependencies**: Use provided fixtures for mocking infrastructure
5. **Test Edge Cases**: Include tests for error conditions and boundary cases

### Performance Considerations

1. **Use Unit Tests for Speed**: Prefer unit tests over integration tests when possible
2. **Parallel Execution**: Use `-n auto` for faster test execution
3. **Selective Testing**: Use markers to run only relevant tests during development
4. **Database Optimization**: Use transactional rollback instead of database recreation

### Debugging Tests

```bash
# Run with verbose output
docker-compose exec backend pytest -v

# Run specific test with debugging
docker-compose exec backend pytest tests/test_device_management.py::test_device_creation -v -s

# Drop into debugger on failure
docker-compose exec backend pytest --pdb

# Run last failed tests
docker-compose exec backend pytest --lf
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart database service
docker-compose restart postgres

# Check database logs
docker-compose logs postgres
```

#### Migration Issues
```bash
# Check current migration status
docker-compose exec backend alembic current

# Run migrations manually
docker-compose exec backend alembic upgrade head

# Reset database (destructive)
docker-compose down -v
docker-compose up -d postgres redis backend
```

#### Permission Issues
```bash
# Check if backend service is running
docker-compose ps backend

# Restart backend service
docker-compose restart backend

# Check backend logs
docker-compose logs backend
```

### Test Isolation Issues

If tests are interfering with each other:

1. Ensure proper use of database fixtures
2. Check for shared state in services
3. Verify mock cleanup in fixtures
4. Consider using separate test markers

## Migration from Legacy Testing

### Removed Components

The following legacy components have been removed:

- Local virtual environment (`venv/`) testing
- Local pytest execution scripts
- Environment-specific test configurations
- Manual database setup scripts

### Updated Commands

| Legacy Command | Docker-Native Command |
|----------------|----------------------|
| `pytest` | `docker-compose exec backend pytest` |
| `python -m pytest` | `docker-compose exec backend pytest` |
| `pytest --cov` | `docker-compose exec backend pytest --cov=app` |
| `./scripts/test.sh` | `./backend/scripts/run_tests.sh` |

### Migration Checklist

- [ ] Remove local `venv/` directory
- [ ] Update CI/CD pipelines to use Docker commands
- [ ] Update developer documentation
- [ ] Train team on new testing workflow
- [ ] Verify all tests pass in Docker environment

## Conclusion

The Docker-native testing strategy provides a robust, consistent, and scalable approach to testing the ISP Framework backend. By running all tests inside Docker containers, we ensure that tests run in the same environment as production, eliminating environment-specific issues and improving reliability.

For questions or issues with the testing setup, please refer to the troubleshooting section or contact the development team.
