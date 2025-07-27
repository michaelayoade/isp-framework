import pytest
from unittest.mock import MagicMock

from app.repositories.customer_service import CustomerServiceRepository, CustomerService


@pytest.fixture
def mock_db():
    """Return a mock SQLAlchemy session object."""
    db = MagicMock()
    # flush and commit should not raise
    db.flush.return_value = None
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def _generate_services(count: int):
    """Create a list of mocked CustomerService objects."""
    return [MagicMock(spec=CustomerService) for _ in range(count)]


def test_commit_batch_exact_multiple(mock_db):
    """commit_batch should flush/commit once per batch size and once at the end."""
    repo = CustomerServiceRepository(mock_db)
    objs = _generate_services(2000)  # Multiple of batch size

    total = repo.commit_batch(objs, batch_size=1000)

    assert total == 2000
    # add called for each object
    assert mock_db.add.call_count == 2000
    # flush/commit called twice (two batches) + final commit (inside helper)
    assert mock_db.flush.call_count == 2
    assert mock_db.commit.call_count == 3


def test_commit_batch_non_multiple(mock_db):
    """commit_batch should handle leftover objects smaller than batch size."""
    repo = CustomerServiceRepository(mock_db)
    objs = _generate_services(2500)  # 2 full batches + 500 leftover

    total = repo.commit_batch(objs, batch_size=1000)

    assert total == 2500
    assert mock_db.add.call_count == 2500
    # flush/commit for 2 batches, plus final commit
    assert mock_db.flush.call_count == 2
    assert mock_db.commit.call_count == 3
