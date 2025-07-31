"""20250731_squashed_baseline

Revision ID: 20250731_squashed_baseline
Revises: 
Create Date: 2025-07-31 16:47:42.313026

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250731_squashed_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Comprehensive baseline migration with all essential schema"""
    
    # Create administrators table (required by many FKs)
    op.create_table(
        'administrators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    # Create customers_extended table (required by many FKs)
    op.create_table(
        'customers_extended',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('login', sa.String(length=50), nullable=False),
        sa.Column('portal_id', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('category', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('login'),
        sa.UniqueConstraint('email')
    )
    
    # Create chart_of_accounts table with unique constraint
    op.create_table(
        'chart_of_accounts',
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_code', name='uq_chart_of_accounts_account_code')
    )
    
    # Add self-referencing foreign key for chart_of_accounts
    op.create_foreign_key(
        'fk_chart_of_accounts_parent', 
        'chart_of_accounts', 
        'chart_of_accounts', 
        ['parent_account_code'], 
        ['account_code']
    )
    
    # Create portal_id_history table (now that customers_extended exists)
    op.create_table(
        'portal_id_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('old_portal_id', sa.String(length=50), nullable=True),
        sa.Column('new_portal_id', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers_extended.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['administrators.id'], ondelete='SET NULL')
    )
    
    # Create essential lookup tables
    op.create_table(
        'customer_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.create_table(
        'service_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.create_table(
        'billing_type',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Insert default data for lookup tables
    op.execute("""
        INSERT INTO customer_status (name, description, is_system) VALUES
        ('Active', 'Customer is active and in good standing', true),
        ('Suspended', 'Customer account is temporarily suspended', true),
        ('Terminated', 'Customer account has been terminated', true),
        ('Pending', 'Customer account is pending activation', true)
        ON CONFLICT (name) DO NOTHING;
    """)
    
    op.execute("""
        INSERT INTO service_type (name, description, is_system) VALUES
        ('Internet', 'Internet connectivity service', true),
        ('VoIP', 'Voice over IP service', true),
        ('IPTV', 'Internet Protocol Television service', true),
        ('Hosting', 'Web hosting service', true)
        ON CONFLICT (name) DO NOTHING;
    """)
    
    op.execute("""
        INSERT INTO billing_type (name, description, is_system) VALUES
        ('Prepaid', 'Pay before service usage', true),
        ('Postpaid', 'Pay after service usage', true),
        ('Credit', 'Credit-based billing', true),
        ('Contract', 'Contract-based billing', true)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Drop all tables created in upgrade"""
    op.drop_table('billing_type')
    op.drop_table('service_type')
    op.drop_table('customer_status')
    op.drop_table('portal_id_history')
    op.drop_constraint('fk_chart_of_accounts_parent', 'chart_of_accounts', type_='foreignkey')
    op.drop_table('chart_of_accounts')
    op.drop_table('customers_extended')
    op.drop_table('administrators')
