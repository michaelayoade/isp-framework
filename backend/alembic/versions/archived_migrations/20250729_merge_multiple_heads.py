"""Merge multiple heads into a single linear history

Revision ID: 20250729_merge_multiple_heads
Revises: 006_enhanced_audit_system, 96fd35845e21, add_provisioning_queue
Create Date: 2025-07-29 19:55:00.000000

This migration does **not** perform any schema changes. It simply merges
three divergent heads so that Alembic sees a single head moving forward.
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401  (imported for Alembic context)
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = '20250729_merge_multiple_heads'
down_revision: Union[str, Sequence[str], None] = (
    '006_enhanced_audit_system',
    '96fd35845e21',
    'add_provisioning_queue',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # pragma: no cover
    """No-op migration."""
    pass


def downgrade() -> None:  # pragma: no cover
    """No-op downgrade."""
    pass
