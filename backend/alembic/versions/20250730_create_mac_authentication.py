"""Create MAC authentication system

Revision ID: 20250730_create_mac_authentication
Revises: 20250730_assign_default_role_permissions
Create Date: 2025-07-30 08:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_mac_authentication'
down_revision = '20250730_assign_default_role_permissions'
branch_labels = None
depends_on = None


def upgrade():
    # Create devices table
    op.create_table('devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('mac_address', sa.String(length=17), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_auto_registered', sa.Boolean(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('last_ip_address', sa.String(length=45), nullable=True),
        sa.Column('last_nas_identifier', sa.String(length=255), nullable=True),
        sa.Column('last_nas_port', sa.String(length=50), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_id'), 'devices', ['id'], unique=False)
    op.create_index(op.f('ix_devices_mac_address'), 'devices', ['mac_address'], unique=True)
    op.create_index('idx_device_customer_status', 'devices', ['customer_id', 'status'], unique=False)
    op.create_index('idx_device_mac_status', 'devices', ['mac_address', 'status'], unique=False)
    op.create_index('idx_device_last_seen', 'devices', ['last_seen'], unique=False)

    # Create device_groups table
    op.create_table('device_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('auto_approve_devices', sa.Boolean(), nullable=True),
        sa.Column('default_device_status', sa.String(length=20), nullable=True),
        sa.Column('bandwidth_limit_mbps', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_device_groups_id'), 'device_groups', ['id'], unique=False)
    op.create_index(op.f('ix_device_groups_customer_id'), 'device_groups', ['customer_id'], unique=False)

    # Create device_group_members table
    op.create_table('device_group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['device_groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_device_group_unique', 'device_group_members', ['device_id', 'group_id'], unique=True)

    # Add MAC authentication columns to customer_services table
    op.add_column('customer_services', sa.Column('mac_auth_enabled', sa.Boolean(), nullable=True))
    op.add_column('customer_services', sa.Column('auto_register_mac', sa.Boolean(), nullable=True))
    op.add_column('customer_services', sa.Column('max_devices', sa.Integer(), nullable=True))

    # Set default values for existing services
    op.execute("UPDATE customer_services SET mac_auth_enabled = false WHERE mac_auth_enabled IS NULL")
    op.execute("UPDATE customer_services SET auto_register_mac = false WHERE auto_register_mac IS NULL")
    op.execute("UPDATE customer_services SET max_devices = 5 WHERE max_devices IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('customer_services', 'mac_auth_enabled', nullable=False)
    op.alter_column('customer_services', 'auto_register_mac', nullable=False)
    op.alter_column('customer_services', 'max_devices', nullable=False)

    # Set default values for device table columns
    op.execute("UPDATE devices SET status = 'pending' WHERE status IS NULL")
    op.execute("UPDATE devices SET is_auto_registered = false WHERE is_auto_registered IS NULL")
    op.execute("UPDATE devices SET is_approved = false WHERE is_approved IS NULL")

    # Make device columns non-nullable after setting defaults
    op.alter_column('devices', 'is_auto_registered', nullable=False)
    op.alter_column('devices', 'is_approved', nullable=False)

    # Set default values for device_groups columns
    op.execute("UPDATE device_groups SET auto_approve_devices = false WHERE auto_approve_devices IS NULL")
    op.execute("UPDATE device_groups SET default_device_status = 'pending' WHERE default_device_status IS NULL")

    # Make device_groups columns non-nullable after setting defaults
    op.alter_column('device_groups', 'auto_approve_devices', nullable=False)
    op.alter_column('device_groups', 'default_device_status', nullable=False)

    # Add RBAC permissions for device management
    op.execute("""
        INSERT INTO permissions (code, name, description, resource, action, category, is_system, created_at)
        VALUES 
        ('devices.view', 'View Devices', 'View customer devices and MAC addresses', 'devices', 'view', 'networking', true, NOW()),
        ('devices.create', 'Create Devices', 'Add new devices and MAC addresses', 'devices', 'create', 'networking', true, NOW()),
        ('devices.update', 'Update Devices', 'Modify device information and settings', 'devices', 'update', 'networking', true, NOW()),
        ('devices.delete', 'Delete Devices', 'Remove devices from the system', 'devices', 'delete', 'networking', true, NOW()),
        ('devices.approve', 'Approve Devices', 'Approve pending device registrations', 'devices', 'approve', 'networking', true, NOW()),
        ('devices.block', 'Block Devices', 'Block or suspend device access', 'devices', 'block', 'networking', true, NOW()),
        ('device_groups.view', 'View Device Groups', 'View device groups and organization', 'device_groups', 'view', 'networking', true, NOW()),
        ('device_groups.create', 'Create Device Groups', 'Create new device groups', 'device_groups', 'create', 'networking', true, NOW()),
        ('device_groups.update', 'Update Device Groups', 'Modify device group settings', 'device_groups', 'update', 'networking', true, NOW()),
        ('device_groups.delete', 'Delete Device Groups', 'Remove device groups', 'device_groups', 'delete', 'networking', true, NOW())
        ON CONFLICT (code) DO NOTHING;
    """)

    # Assign device permissions to relevant roles
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code IN ('super_admin', 'admin', 'technician') 
        AND p.code IN ('devices.view', 'devices.create', 'devices.update', 'devices.delete', 'devices.approve', 'devices.block',
                       'device_groups.view', 'device_groups.create', 'device_groups.update', 'device_groups.delete')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Assign limited device permissions to customer support
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'customer_support'
        AND p.code IN ('devices.view', 'devices.approve', 'devices.block')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Assign read-only device permissions to read_only role
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'read_only'
        AND p.code IN ('devices.view', 'device_groups.view')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)


def downgrade():
    # Remove RBAC permissions
    op.execute("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code LIKE 'devices.%' OR code LIKE 'device_groups.%')")
    op.execute("DELETE FROM permissions WHERE code LIKE 'devices.%' OR code LIKE 'device_groups.%'")

    # Remove MAC authentication columns from customer_services
    op.drop_column('customer_services', 'max_devices')
    op.drop_column('customer_services', 'auto_register_mac')
    op.drop_column('customer_services', 'mac_auth_enabled')

    # Drop device tables
    op.drop_index('idx_device_group_unique', table_name='device_group_members')
    op.drop_table('device_group_members')
    op.drop_index(op.f('ix_device_groups_customer_id'), table_name='device_groups')
    op.drop_index(op.f('ix_device_groups_id'), table_name='device_groups')
    op.drop_table('device_groups')
    op.drop_index('idx_device_last_seen', table_name='devices')
    op.drop_index('idx_device_mac_status', table_name='devices')
    op.drop_index('idx_device_customer_status', table_name='devices')
    op.drop_index(op.f('ix_devices_mac_address'), table_name='devices')
    op.drop_index(op.f('ix_devices_id'), table_name='devices')
    op.drop_table('devices')
