"""Create billing types lookup table

Revision ID: 20250730_create_billing_types
Revises: 20250730_create_ticket_statuses
Create Date: 2025-07-30 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_billing_types'
down_revision = '20250730_create_ticket_statuses'
branch_labels = None
depends_on = None


def upgrade():
    # Create billing_types table
    op.create_table('billing_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('requires_prepayment', sa.Boolean(), nullable=True),
        sa.Column('supports_prorating', sa.Boolean(), nullable=True),
        sa.Column('default_cycle_days', sa.Integer(), nullable=True),
        sa.Column('allows_partial_payments', sa.Boolean(), nullable=True),
        sa.Column('auto_suspend_on_overdue', sa.Boolean(), nullable=True),
        sa.Column('grace_period_days', sa.Integer(), nullable=True),
        sa.Column('supports_credit_limit', sa.Boolean(), nullable=True),
        sa.Column('default_credit_limit', sa.Integer(), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_billing_types_id'), 'billing_types', ['id'], unique=False)
    op.create_index(op.f('ix_billing_types_code'), 'billing_types', ['code'], unique=True)
    
    # Insert default billing types
    billing_types_table = sa.table('billing_types',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('is_recurring', sa.Boolean),
        sa.column('requires_prepayment', sa.Boolean),
        sa.column('supports_prorating', sa.Boolean),
        sa.column('default_cycle_days', sa.Integer),
        sa.column('allows_partial_payments', sa.Boolean),
        sa.column('auto_suspend_on_overdue', sa.Boolean),
        sa.column('grace_period_days', sa.Integer),
        sa.column('supports_credit_limit', sa.Boolean),
        sa.column('default_credit_limit', sa.Integer),
        sa.column('color_hex', sa.String),
        sa.column('icon_name', sa.String)
    )
    
    op.bulk_insert(billing_types_table, [
        {
            'code': 'recurring',
            'name': 'Recurring Monthly',
            'description': 'Standard monthly recurring billing',
            'is_active': True,
            'is_system': True,
            'sort_order': 1,
            'is_recurring': True,
            'requires_prepayment': False,
            'supports_prorating': True,
            'default_cycle_days': 30,
            'allows_partial_payments': False,
            'auto_suspend_on_overdue': True,
            'grace_period_days': 3,
            'supports_credit_limit': False,
            'default_credit_limit': 0,
            'color_hex': '#3B82F6',  # Blue
            'icon_name': 'calendar'
        },
        {
            'code': 'prepaid_monthly',
            'name': 'Prepaid Monthly',
            'description': 'Monthly service paid in advance',
            'is_active': True,
            'is_system': True,
            'sort_order': 2,
            'is_recurring': True,
            'requires_prepayment': True,
            'supports_prorating': False,
            'default_cycle_days': 30,
            'allows_partial_payments': False,
            'auto_suspend_on_overdue': True,
            'grace_period_days': 0,
            'supports_credit_limit': False,
            'default_credit_limit': 0,
            'color_hex': '#10B981',  # Green
            'icon_name': 'credit-card'
        },
        {
            'code': 'prepaid_daily',
            'name': 'Prepaid Daily',
            'description': 'Daily service paid in advance',
            'is_active': True,
            'is_system': True,
            'sort_order': 3,
            'is_recurring': True,
            'requires_prepayment': True,
            'supports_prorating': False,
            'default_cycle_days': 1,
            'allows_partial_payments': False,
            'auto_suspend_on_overdue': True,
            'grace_period_days': 0,
            'supports_credit_limit': True,
            'default_credit_limit': 1000,  # $10.00 in cents
            'color_hex': '#F59E0B',  # Amber
            'icon_name': 'clock'
        },
        {
            'code': 'postpaid',
            'name': 'Postpaid',
            'description': 'Service billed after usage with credit limit',
            'is_active': True,
            'is_system': True,
            'sort_order': 4,
            'is_recurring': True,
            'requires_prepayment': False,
            'supports_prorating': True,
            'default_cycle_days': 30,
            'allows_partial_payments': True,
            'auto_suspend_on_overdue': False,
            'grace_period_days': 7,
            'supports_credit_limit': True,
            'default_credit_limit': 10000,  # $100.00 in cents
            'color_hex': '#8B5CF6',  # Purple
            'icon_name': 'trending-up'
        },
        {
            'code': 'one_time',
            'name': 'One-Time Payment',
            'description': 'Single payment for services or products',
            'is_active': True,
            'is_system': True,
            'sort_order': 5,
            'is_recurring': False,
            'requires_prepayment': True,
            'supports_prorating': False,
            'default_cycle_days': 0,
            'allows_partial_payments': False,
            'auto_suspend_on_overdue': False,
            'grace_period_days': 0,
            'supports_credit_limit': False,
            'default_credit_limit': 0,
            'color_hex': '#EF4444',  # Red
            'icon_name': 'dollar-sign'
        },
        {
            'code': 'usage_based',
            'name': 'Usage-Based Billing',
            'description': 'Billing based on actual usage/consumption',
            'is_active': True,
            'is_system': False,
            'sort_order': 6,
            'is_recurring': True,
            'requires_prepayment': False,
            'supports_prorating': True,
            'default_cycle_days': 30,
            'allows_partial_payments': True,
            'auto_suspend_on_overdue': True,
            'grace_period_days': 5,
            'supports_credit_limit': True,
            'default_credit_limit': 5000,  # $50.00 in cents
            'color_hex': '#06B6D4',  # Cyan
            'icon_name': 'activity'
        }
    ])
    
    # Add billing_type_id column to customers table if it exists
    try:
        op.add_column('customers', sa.Column('billing_type_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'customers', 'billing_types', ['billing_type_id'], ['id'])
        
        # Migrate existing billing_type string values to billing_type_id
        op.execute("""
            UPDATE customers 
            SET billing_type_id = (
                SELECT id FROM billing_types 
                WHERE billing_types.code = customers.billing_type
            )
            WHERE billing_type IN ('recurring', 'prepaid_monthly', 'prepaid_daily', 'postpaid', 'one_time', 'usage_based')
        """)
        
        # Set default billing_type_id to 'recurring' (id=1) for any remaining NULL values
        op.execute("UPDATE customers SET billing_type_id = 1 WHERE billing_type_id IS NULL")
        
        # Make billing_type_id NOT NULL after migration
        op.alter_column('customers', 'billing_type_id', nullable=False)
        
        # Drop the old billing_type string column
        op.drop_column('customers', 'billing_type')
    except Exception:
        # customers table doesn't have billing_type column yet, skip this part
        pass
    
    # Add billing_type_id column to service_plans table if it exists
    try:
        op.add_column('service_plans', sa.Column('billing_type_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'service_plans', 'billing_types', ['billing_type_id'], ['id'])
        
        # Migrate existing billing_type string values to billing_type_id
        op.execute("""
            UPDATE service_plans 
            SET billing_type_id = (
                SELECT id FROM billing_types 
                WHERE billing_types.code = service_plans.billing_type
            )
            WHERE billing_type IN ('recurring', 'prepaid_monthly', 'prepaid_daily', 'postpaid', 'one_time', 'usage_based')
        """)
        
        # Set default billing_type_id to 'recurring' (id=1) for any remaining NULL values
        op.execute("UPDATE service_plans SET billing_type_id = 1 WHERE billing_type_id IS NULL")
        
        # Make billing_type_id NOT NULL after migration
        op.alter_column('service_plans', 'billing_type_id', nullable=False)
        
        # Drop the old billing_type string column
        op.drop_column('service_plans', 'billing_type')
    except Exception:
        # service_plans table doesn't have billing_type column yet, skip this part
        pass


def downgrade():
    # Add back the billing_type string column to customers if it exists
    try:
        op.add_column('customers', sa.Column('billing_type', sa.String(length=50), nullable=True))
        
        # Migrate billing_type_id back to string values
        op.execute("""
            UPDATE customers 
            SET billing_type = (
                SELECT code FROM billing_types 
                WHERE billing_types.id = customers.billing_type_id
            )
        """)
        
        # Set default for any NULL values
        op.execute("UPDATE customers SET billing_type = 'recurring' WHERE billing_type IS NULL")
        
        # Make billing_type NOT NULL and drop foreign key
        op.alter_column('customers', 'billing_type', nullable=False)
        op.drop_constraint(None, 'customers', type_='foreignkey')
        op.drop_column('customers', 'billing_type_id')
    except Exception:
        # customers table doesn't exist, skip this part
        pass
    
    # Add back the billing_type string column to service_plans if it exists
    try:
        op.add_column('service_plans', sa.Column('billing_type', sa.String(length=50), nullable=True))
        
        # Migrate billing_type_id back to string values
        op.execute("""
            UPDATE service_plans 
            SET billing_type = (
                SELECT code FROM billing_types 
                WHERE billing_types.id = service_plans.billing_type_id
            )
        """)
        
        # Set default for any NULL values
        op.execute("UPDATE service_plans SET billing_type = 'recurring' WHERE billing_type IS NULL")
        
        # Make billing_type NOT NULL and drop foreign key
        op.alter_column('service_plans', 'billing_type', nullable=False)
        op.drop_constraint(None, 'service_plans', type_='foreignkey')
        op.drop_column('service_plans', 'billing_type_id')
    except Exception:
        # service_plans table doesn't exist, skip this part
        pass
    
    # Drop billing_types table
    op.drop_index(op.f('ix_billing_types_code'), table_name='billing_types')
    op.drop_index(op.f('ix_billing_types_id'), table_name='billing_types')
    op.drop_table('billing_types')
