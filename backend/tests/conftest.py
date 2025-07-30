"""Docker-native pytest fixtures for ISP Framework backend tests.

This module provides comprehensive test fixtures optimized for Docker container execution
with proper database isolation, RBAC setup, and infrastructure mocking.
"""
import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.main import app
from app.core.database import Base, get_db
from app.models.admin.base import Administrator
from app.models.rbac.models import Role, Permission, UserRole
from app.core.security import get_password_hash


# Docker-native test database configuration
# Uses the same Postgres container but separate schema per test session
TEST_SCHEMA = f"pytest_{os.getenv('PYTEST_XDIST_WORKER', 'main')}"
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/isp_framework", f"/isp_framework")

# Create engines for both sync and async operations
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "options": f"-c search_path={TEST_SCHEMA},public -c timezone=utc"
    },
    poolclass=StaticPool,
    echo=False
)

async_test_engine = create_async_engine(
    TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    connect_args={
        "server_settings": {
            "search_path": f"{TEST_SCHEMA},public",
            "timezone": "utc"
        }
    },
    echo=False
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
AsyncTestingSessionLocal = sessionmaker(
    bind=async_test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test schema and tables at session start, cleanup afterwards."""
    # Create test schema
    with test_engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
        conn.commit()
    
    # Create all tables in test schema
    Base.metadata.create_all(bind=test_engine)
    
    yield
    
    # Cleanup: drop test schema
    with test_engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
        conn.commit()


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Provide a transactional database session for each test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async transactional database session for each test function."""
    async with async_test_engine.begin() as conn:
        async_session = AsyncTestingSessionLocal(bind=conn)
        try:
            yield async_session
        finally:
            await async_session.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(async_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing async endpoints."""
    async def override_get_db():
        yield async_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def super_admin(db_session) -> Administrator:
    """Create a super admin user for RBAC tests."""
    # Create super admin role if it doesn't exist
    super_admin_role = db_session.query(Role).filter_by(code="super_admin").first()
    if not super_admin_role:
        super_admin_role = Role(
            code="super_admin",
            name="Super Administrator",
            description="Full system access with all permissions",
            is_system=True,
            is_admin_role=True
        )
        db_session.add(super_admin_role)
        db_session.flush()
    
    # Create super admin user
    admin = Administrator(
        username="test_super_admin",
        email="super@test.com",
        full_name="Test Super Admin",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin)
    db_session.flush()
    
    # Assign super admin role
    user_role = UserRole(
        user_id=admin.id,
        role_id=super_admin_role.id,
        is_active=True
    )
    db_session.add(user_role)
    db_session.commit()
    
    return admin


@pytest.fixture(scope="function")
def regular_admin(db_session) -> Administrator:
    """Create a regular admin user for testing."""
    admin_role = db_session.query(Role).filter_by(code="admin").first()
    if not admin_role:
        admin_role = Role(
            code="admin",
            name="Administrator",
            description="Administrative access to most features",
            is_system=True,
            is_admin_role=True
        )
        db_session.add(admin_role)
        db_session.flush()
    
    admin = Administrator(
        username="test_admin",
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(admin)
    db_session.flush()
    
    user_role = UserRole(
        user_id=admin.id,
        role_id=admin_role.id,
        is_active=True
    )
    db_session.add(user_role)
    db_session.commit()
    
    return admin


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis for caching and quota tests."""
    try:
        import fakeredis
        return fakeredis.FakeRedis(decode_responses=True)
    except ImportError:
        # Fallback to MagicMock if fakeredis not available
        return MagicMock()


@pytest.fixture(scope="function")
def mock_minio():
    """Mock MinIO S3 client for file storage tests."""
    return MagicMock()


@pytest.fixture(scope="function")
def mock_ansible_runner():
    """Mock Ansible runner for automation tests."""
    mock_runner = MagicMock()
    mock_runner.run.return_value.status = "successful"
    mock_runner.run.return_value.rc = 0
    mock_runner.run.return_value.stdout = "Task completed successfully"
    return mock_runner


@pytest.fixture(scope="function")
def auth_headers(super_admin) -> dict:
    """Generate authentication headers for API tests."""
    from app.core.security import create_access_token
    
    token = create_access_token(
        data={"sub": super_admin.username, "admin_id": super_admin.id}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def sample_customer_data() -> dict:
    """Sample customer data for testing."""
    return {
        "name": "Test Customer",
        "email": "customer@test.com",
        "phone": "+1234567890",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "TS",
        "zip_code": "12345",
        "country": "Test Country"
    }


@pytest.fixture(scope="function")
def sample_device_data() -> dict:
    """Sample device data for MAC authentication tests."""
    return {
        "mac_address": "00:11:22:33:44:55",
        "name": "Test Device",
        "description": "Test IoT Device",
        "device_type": "iot_sensor"
    }
