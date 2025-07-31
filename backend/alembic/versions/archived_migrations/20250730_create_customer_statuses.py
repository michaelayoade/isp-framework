"""Create customer statuses lookup table

Revision ID: 20250730_create_customer_statuses
Revises: 20250730_create_contact_types
Create Date: 2025-07-30 07:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_customer_statuses'
down_revision = '20250730_create_contact_types'
branch_labels = None
depends_on = None


def upgrade():
    # Create customer_statuses table
    op.create_table('customer_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('allows_service_activation', sa.Boolean(), nullable=True),
        sa.Column('allows_billing', sa.Boolean(), nullable=True),
        sa.Column('is_terminal', sa.Boolean(), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_statuses_id'), 'customer_statuses', ['id'], unique=False)
    op.create_index(op.f('ix_customer_statuses_code'), 'customer_statuses', ['code'], unique=True)
    
    # Insert default customer statuses
    customer_statuses_table = sa.table('customer_statuses',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('allows_service_activation', sa.Boolean),
        sa.column('allows_billing', sa.Boolean),
        sa.column('is_terminal', sa.Boolean),
        sa.column('color_hex', sa.String),
        sa.column('icon_name', sa.String)
    )
    
    op.bulk_insert(customer_statuses_table, [
        {
            'code': 'new',
            'name': 'New Customer',
            'description': 'Recently registered customer, pending activation',
            'is_active': True,
            'is_system': True,
            'sort_order': 1,
            'allows_service_activation': False,
            'allows_billing': False,
            'is_terminal': False,
            'color_hex': '#3B82F6',  # Blue
            'icon_name': 'user-plus'
        },
        {
            'code': 'active',
            'name': 'Active',
            'description': 'Active customer with services running',
            'is_active': True,
            'is_system': True,
            'sort_order': 2,
            'allows_service_activation': True,
            'allows_billing': True,
            'is_terminal': False,
            'color_hex': '#10B981',  # Green
            'icon_name': 'check-circle'
        },
        {
            'code': 'suspended',
            'name': 'Suspended',
            'description': 'Services temporarily suspended (usually for non-payment)',
            'is_active': True,
            'is_system': True,
            'sort_order': 3,
            'allows_service_activation': False,
            'allows_billing': True,
            'is_terminal': False,
            'color_hex': '#F59E0B',  # Amber
            'icon_name': 'pause-circle'
        },
        {
            'code': 'blocked',
            'name': 'Blocked',
            'description': 'Customer blocked due to policy violation or abuse',
            'is_active': True,
            'is_system': True,
            'sort_order': 4,
            'allows_service_activation': False,
            'allows_billing': False,
            'is_terminal': False,
            'color_hex': '#EF4444',  # Red
            'icon_name': 'x-circle'
        },
        {
            'code': 'terminated',
            'name': 'Terminated',
            'description': 'Customer account permanently closed',
            'is_active': True,
            'is_system': True,
            'sort_order': 5,
            'allows_service_activation': False,
            'allows_billing': False,
            'is_terminal': True,
            'color_hex': '#6B7280',  # Gray
            'icon_name': 'minus-circle'
        },
        {
            'code': 'prospect',
            'name': 'Prospect',
            'description': 'Potential customer in sales pipeline',
            'is_active': True,
            'is_system': False,
            'sort_order': 0,
            'allows_service_activation': False,
            'allows_billing': False,
            'is_terminal': False,
            'color_hex': '#8B5CF6',  # Purple
            'icon_name': 'eye'
        }
    ])
    
    # Add status_id column to customers table
    op.add_column('customers', sa.Column('status_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'customers', 'customer_statuses', ['status_id'], ['id'])
    
    # Migrate existing status string values to status_id
    # First, update existing records to use appropriate status IDs based on string values
    op.execute("""
        UPDATE customers 
        SET status_id = (
            SELECT id FROM customer_statuses 
            WHERE customer_statuses.code = customers.status
        )
        WHERE status IN ('new', 'active', 'suspended', 'blocked', 'terminated')
    """)
    
    # Set any remaining NULL status_id to 'active' (id=2)
    op.execute("UPDATE customers SET status_id = 2 WHERE status_id IS NULL")
    
    # Make status_id NOT NULL after migration
    op.alter_column('customers', 'status_id', nullable=False)
    
    # Drop the old status string column
    op.drop_column('customers', 'status')


def downgrade():
    # Add back the status string column
    op.add_column('customers', sa.Column('status', sa.String(length=20), nullable=True))
    
    # Migrate status_id back to string values
    op.execute("""
        UPDATE customers 
        SET status = (
            SELECT code FROM customer_statuses 
            WHERE customer_statuses.id = customers.status_id
        )
    """)
    
    # Set default for any NULL values
    op.execute("UPDATE customers SET status = 'active' WHERE status IS NULL")
    
    # Make status NOT NULL and drop foreign key
    op.alter_column('customers', 'status', nullable=False)
    op.drop_constraint(None, 'customers', type_='foreignkey')
    op.drop_column('customers', 'status_id')
    
    # Drop customer_statuses table
    op.drop_index(op.f('ix_customer_statuses_code'), table_name='customer_statuses')
    op.drop_index(op.f('ix_customer_statuses_id'), table_name='customer_statuses')
    op.drop_table('customer_statuses')
