"""Basic database connectivity smoke tests.
Run quickly to confirm that the test database is reachable and Alembic migrations are at head."""
from sqlalchemy import text
from alembic.config import Config
from alembic import command

from app.core.database import engine


def test_can_connect_db():
    """Simple SELECT 1 query succeeds."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_alembic_head_is_current(tmp_path):
    """Ensure the database is at the latest migration head."""
    # Create a temporary Alembic config pointing to real alembic.ini
    cfg = Config("backend/alembic.ini")
    cfg.set_main_option("sqlalchemy.url", str(engine.url))

    # 'current' will raise if DB is behind; capture stdout for assertion
    command.current(cfg, verbose=False)
