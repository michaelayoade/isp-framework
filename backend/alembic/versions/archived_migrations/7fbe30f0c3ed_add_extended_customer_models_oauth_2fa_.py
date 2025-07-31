"""Add extended customer models, OAuth, 2FA, and API key models

Revision ID: 7fbe30f0c3ed
Revises: 
Create Date: 2025-07-23 12:26:11.160384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fbe30f0c3ed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op; changes already applied in earlier migrations or base schema.
    pass


def downgrade() -> None:
    # No-op corresponding to upgrade pass.
    pass
