"""fix_chart_of_accounts_constraint

Revision ID: 20250730_fix_chart_of_accounts_constraint
Revises: 11e9e8a09b65
Create Date: 2025-07-30 12:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250730_fix_chart_of_accounts_constraint'
down_revision: Union[str, None] = '11e9e8a09b65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint to chart_of_accounts.account_code to support self-referencing FK"""
    
    # Create chart_of_accounts table if it doesn't exist
    op.create_table('chart_of_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_code', sa.String(length=20), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('account_type', sa.String(length=50), nullable=False),
        sa.Column('parent_account_code', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.String(length=10), nullable=False),
        sa.Column('is_system_account', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add unique constraint on account_code (required for self-referencing FK)
    op.create_unique_constraint('uq_chart_of_accounts_account_code', 'chart_of_accounts', ['account_code'])
    
    # Add index on account_code for performance
    op.create_index(op.f('ix_chart_of_accounts_account_code'), 'chart_of_accounts', ['account_code'], unique=True)
    
    # Add index on id
    op.create_index(op.f('ix_chart_of_accounts_id'), 'chart_of_accounts', ['id'], unique=False)
    
    # Now add the self-referencing foreign key constraint
    op.create_foreign_key('fk_chart_of_accounts_parent', 'chart_of_accounts', 'chart_of_accounts', ['parent_account_code'], ['account_code'])


def downgrade() -> None:
    """Remove chart_of_accounts table and constraints"""
    
    # Drop foreign key constraint first
    op.drop_constraint('fk_chart_of_accounts_parent', 'chart_of_accounts', type_='foreignkey')
    
    # Drop indexes
    op.drop_index(op.f('ix_chart_of_accounts_id'), table_name='chart_of_accounts')
    op.drop_index(op.f('ix_chart_of_accounts_account_code'), table_name='chart_of_accounts')
    
    # Drop unique constraint
    op.drop_constraint('uq_chart_of_accounts_account_code', 'chart_of_accounts', type_='unique')
    
    # Drop table
    op.drop_table('chart_of_accounts')
