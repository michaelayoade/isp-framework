"""Create service types lookup table

Revision ID: 20250730_create_service_types
Revises: 20250730_create_customer_statuses
Create Date: 2025-07-30 07:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_service_types'
down_revision = '20250730_create_customer_statuses'
branch_labels = None
depends_on = None


def upgrade():
    # Create service_types table
    op.create_table('service_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('requires_installation', sa.Boolean(), nullable=True),
        sa.Column('supports_bandwidth_limits', sa.Boolean(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('allows_multiple_instances', sa.Boolean(), nullable=True),
        sa.Column('default_billing_cycle', sa.String(length=20), nullable=True),
        sa.Column('requires_equipment', sa.Boolean(), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('provisioning_template', sa.String(length=100), nullable=True),
        sa.Column('qos_profile', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_types_id'), 'service_types', ['id'], unique=False)
    op.create_index(op.f('ix_service_types_code'), 'service_types', ['code'], unique=True)
    
    # Insert default service types
    service_types_table = sa.table('service_types',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('requires_installation', sa.Boolean),
        sa.column('supports_bandwidth_limits', sa.Boolean),
        sa.column('is_recurring', sa.Boolean),
        sa.column('allows_multiple_instances', sa.Boolean),
        sa.column('default_billing_cycle', sa.String),
        sa.column('requires_equipment', sa.Boolean),
        sa.column('color_hex', sa.String),
        sa.column('icon_name', sa.String),
        sa.column('provisioning_template', sa.String),
        sa.column('qos_profile', sa.String)
    )
    
    op.bulk_insert(service_types_table, [
        {
            'code': 'internet',
            'name': 'Internet Service',
            'description': 'Broadband internet connectivity service',
            'is_active': True,
            'is_system': True,
            'sort_order': 1,
            'requires_installation': True,
            'supports_bandwidth_limits': True,
            'is_recurring': True,
            'allows_multiple_instances': False,
            'default_billing_cycle': 'monthly',
            'requires_equipment': True,
            'color_hex': '#3B82F6',  # Blue
            'icon_name': 'wifi',
            'provisioning_template': 'internet_basic',
            'qos_profile': 'residential'
        },
        {
            'code': 'voip',
            'name': 'VoIP Phone Service',
            'description': 'Voice over IP telephone service',
            'is_active': True,
            'is_system': True,
            'sort_order': 2,
            'requires_installation': True,
            'supports_bandwidth_limits': False,
            'is_recurring': True,
            'allows_multiple_instances': True,
            'default_billing_cycle': 'monthly',
            'requires_equipment': True,
            'color_hex': '#10B981',  # Green
            'icon_name': 'phone',
            'provisioning_template': 'voip_basic',
            'qos_profile': 'voice'
        },
        {
            'code': 'tv',
            'name': 'TV Service',
            'description': 'Digital television and streaming service',
            'is_active': True,
            'is_system': True,
            'sort_order': 3,
            'requires_installation': True,
            'supports_bandwidth_limits': True,
            'is_recurring': True,
            'allows_multiple_instances': False,
            'default_billing_cycle': 'monthly',
            'requires_equipment': True,
            'color_hex': '#F59E0B',  # Amber
            'icon_name': 'tv',
            'provisioning_template': 'tv_basic',
            'qos_profile': 'video'
        },
        {
            'code': 'hosting',
            'name': 'Web Hosting',
            'description': 'Website hosting and domain services',
            'is_active': True,
            'is_system': True,
            'sort_order': 4,
            'requires_installation': False,
            'supports_bandwidth_limits': True,
            'is_recurring': True,
            'allows_multiple_instances': True,
            'default_billing_cycle': 'monthly',
            'requires_equipment': False,
            'color_hex': '#8B5CF6',  # Purple
            'icon_name': 'server',
            'provisioning_template': 'hosting_basic',
            'qos_profile': 'data'
        },
        {
            'code': 'support',
            'name': 'Technical Support',
            'description': 'Premium technical support service',
            'is_active': True,
            'is_system': True,
            'sort_order': 5,
            'requires_installation': False,
            'supports_bandwidth_limits': False,
            'is_recurring': True,
            'allows_multiple_instances': False,
            'default_billing_cycle': 'monthly',
            'requires_equipment': False,
            'color_hex': '#EF4444',  # Red
            'icon_name': 'headphones',
            'provisioning_template': None,
            'qos_profile': None
        },
        {
            'code': 'installation',
            'name': 'Installation Service',
            'description': 'One-time installation and setup service',
            'is_active': True,
            'is_system': False,
            'sort_order': 6,
            'requires_installation': False,
            'supports_bandwidth_limits': False,
            'is_recurring': False,
            'allows_multiple_instances': True,
            'default_billing_cycle': 'one_time',
            'requires_equipment': False,
            'color_hex': '#6B7280',  # Gray
            'icon_name': 'wrench',
            'provisioning_template': 'installation_basic',
            'qos_profile': None
        }
    ])
    
    # Add service_type_id column to service_plans table if it exists
    # Note: This assumes service_plans table exists, if not this will be handled in service plan migration
    try:
        op.add_column('service_plans', sa.Column('service_type_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'service_plans', 'service_types', ['service_type_id'], ['id'])
        
        # Migrate existing service_type string values to service_type_id
        op.execute("""
            UPDATE service_plans 
            SET service_type_id = (
                SELECT id FROM service_types 
                WHERE service_types.code = service_plans.service_type
            )
            WHERE service_type IN ('internet', 'voip', 'tv', 'hosting', 'support', 'installation')
        """)
        
        # Set default service_type_id to 'internet' (id=1) for any remaining NULL values
        op.execute("UPDATE service_plans SET service_type_id = 1 WHERE service_type_id IS NULL")
        
        # Make service_type_id NOT NULL after migration
        op.alter_column('service_plans', 'service_type_id', nullable=False)
        
        # Drop the old service_type string column
        op.drop_column('service_plans', 'service_type')
    except Exception:
        # service_plans table doesn't exist yet, skip this part
        pass


def downgrade():
    # Add back the service_type string column to service_plans if it exists
    try:
        op.add_column('service_plans', sa.Column('service_type', sa.String(length=50), nullable=True))
        
        # Migrate service_type_id back to string values
        op.execute("""
            UPDATE service_plans 
            SET service_type = (
                SELECT code FROM service_types 
                WHERE service_types.id = service_plans.service_type_id
            )
        """)
        
        # Set default for any NULL values
        op.execute("UPDATE service_plans SET service_type = 'internet' WHERE service_type IS NULL")
        
        # Make service_type NOT NULL and drop foreign key
        op.alter_column('service_plans', 'service_type', nullable=False)
        op.drop_constraint(None, 'service_plans', type_='foreignkey')
        op.drop_column('service_plans', 'service_type_id')
    except Exception:
        # service_plans table doesn't exist, skip this part
        pass
    
    # Drop service_types table
    op.drop_index(op.f('ix_service_types_code'), table_name='service_types')
    op.drop_index(op.f('ix_service_types_id'), table_name='service_types')
    op.drop_table('service_types')
