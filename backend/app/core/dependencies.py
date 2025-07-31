"""
Core dependencies for FastAPI dependency injection.

This module provides common dependency functions used across the application,
particularly for database session management and authentication.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields:
        Session: SQLAlchemy database session

    Note:
        The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
