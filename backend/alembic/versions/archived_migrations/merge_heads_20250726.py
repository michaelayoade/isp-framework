"""merge heads 2025-07-26

Revision ID: merge_heads_20250726
Revises: create_dead_letter_queue_tables, settings_001, fix_radius_foreign_keys
Create Date: 2025-07-26 16:00:00.000000

This is an automatically generated *merge* revision to reconcile multiple
concurrent heads produced during parallel development.  It does **not**
perform any schema changes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa: F401  (imported for Alembic context)

# revision identifiers, used by Alembic.
revision: str = 'merge_heads_20250726'
down_revision: Union[str, Sequence[str], None] = (
    'create_dead_letter_queue_tables',
    'settings_001',
    'fix_radius_foreign_keys',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op."""
    pass


def downgrade() -> None:
    """No-op."""
    pass
