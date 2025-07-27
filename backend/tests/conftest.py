"""Common pytest fixtures for ISP Framework backend tests."""
import asyncio
import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.main import app
from app.core.database import Base


SQLALCHEMY_TEST_URL = settings.DATABASE_URL + "_test"  # simple pattern, ensure env prepared
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"options": "-c timezone=utc"})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _prepare_test_db():
    """Create all tables at test session start and drop afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Yield a transactional DB session for a test function."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):  # noqa: D401 – fixture dependency
    """FastAPI TestClient with overridden DB dependency."""
    from app.core.dependencies import get_db  # import here to avoid circular

    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
