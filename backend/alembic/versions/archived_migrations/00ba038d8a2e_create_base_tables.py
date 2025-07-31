"""Create base tables

Revision ID: 00ba038d8a2e
Revises: 008_add_radius_clients
Create Date: 2025-07-23 23:23:26.638251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00ba038d8a2e'
down_revision: Union[str, None] = '008_add_radius_clients'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
