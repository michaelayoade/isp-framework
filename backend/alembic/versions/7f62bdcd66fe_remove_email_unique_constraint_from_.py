"""remove_email_unique_constraint_from_customers

Revision ID: 7f62bdcd66fe
Revises: db51b622cd6f
Create Date: 2025-08-01 14:59:50.470813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f62bdcd66fe'
down_revision: Union[str, None] = 'db51b622cd6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove unique constraint on email from customers table
    op.drop_constraint('customers_email_key', 'customers', type_='unique')


def downgrade() -> None:
    # Re-add unique constraint on email to customers table
    op.create_unique_constraint('customers_email_key', 'customers', ['email'])
