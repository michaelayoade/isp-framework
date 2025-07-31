"""fix_chart_of_accounts_constraint

Revision ID: 20250730_fix_chart_of_accounts_constraint
Revises: 20250729_merge_multiple_heads
Create Date: 2025-07-30 12:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250730_fix_chart_of_accounts_constraint'
down_revision: Union[str, None] = '20250729_merge_multiple_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to chart_of_accounts.account_code to support self-referencing FK"""
    
    # Add unique constraint on account_code (required for self-referencing FK)
    # This works for both fresh and existing databases
    op.create_unique_constraint(
        'uq_chart_of_accounts_account_code', 
        'chart_of_accounts', 
        ['account_code']
    )


def downgrade() -> None:
    """Remove unique constraint from chart_of_accounts.account_code"""
    
    # Drop unique constraint
    op.drop_constraint('uq_chart_of_accounts_account_code', 'chart_of_accounts', type_='unique')
