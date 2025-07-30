"""Create RBAC system (roles, permissions, relationships)

Revision ID: 20250730_create_rbac_system
Revises: 20250730_create_billing_types
Create Date: 2025-07-30 08:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_rbac_system'
down_revision = 'merge_heads_20250726'
branch_labels = None
depends_on = None


def upgrade():
    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_permissions_id'), 'permissions', ['id'], unique=False)
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    op.create_index(op.f('ix_permissions_category'), 'permissions', ['category'], unique=False)
    
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_admin_role', sa.Boolean(), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_code'), 'roles', ['code'], unique=True)
    
    # Create role_permissions table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    op.create_index(op.f('ix_role_permissions_id'), 'role_permissions', ['id'], unique=False)
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['administrators.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    
    # Insert default permissions
    permissions_table = sa.table('permissions',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('category', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('resource', sa.String),
        sa.column('action', sa.String),
        sa.column('scope', sa.String),
        sa.column('icon_name', sa.String)
    )
    
    # Define comprehensive permission set
    permissions_data = [
        # Dashboard permissions
        {'code': 'dashboard.view', 'name': 'View Dashboard', 'description': 'Access main dashboard', 'category': 'dashboard', 'resource': 'dashboard', 'action': 'view', 'scope': 'all', 'icon_name': 'home', 'sort_order': 1},
        {'code': 'dashboard.analytics', 'name': 'View Analytics', 'description': 'Access analytics and reports', 'category': 'dashboard', 'resource': 'analytics', 'action': 'view', 'scope': 'all', 'icon_name': 'bar-chart', 'sort_order': 2},
        
        # Customer management permissions
        {'code': 'customers.view', 'name': 'View Customers', 'description': 'View customer list and details', 'category': 'customers', 'resource': 'customers', 'action': 'view', 'scope': 'all', 'icon_name': 'users', 'sort_order': 10},
        {'code': 'customers.create', 'name': 'Create Customers', 'description': 'Add new customers', 'category': 'customers', 'resource': 'customers', 'action': 'create', 'scope': 'all', 'icon_name': 'user-plus', 'sort_order': 11},
        {'code': 'customers.update', 'name': 'Update Customers', 'description': 'Edit customer information', 'category': 'customers', 'resource': 'customers', 'action': 'update', 'scope': 'all', 'icon_name': 'edit', 'sort_order': 12},
        {'code': 'customers.delete', 'name': 'Delete Customers', 'description': 'Remove customers', 'category': 'customers', 'resource': 'customers', 'action': 'delete', 'scope': 'all', 'icon_name': 'trash', 'sort_order': 13},
        {'code': 'customers.export', 'name': 'Export Customers', 'description': 'Export customer data', 'category': 'customers', 'resource': 'customers', 'action': 'export', 'scope': 'all', 'icon_name': 'download', 'sort_order': 14},
        
        # Billing permissions
        {'code': 'billing.view', 'name': 'View Billing', 'description': 'Access billing information', 'category': 'billing', 'resource': 'billing', 'action': 'view', 'scope': 'all', 'icon_name': 'credit-card', 'sort_order': 20},
        {'code': 'invoices.view', 'name': 'View Invoices', 'description': 'View invoice list and details', 'category': 'billing', 'resource': 'invoices', 'action': 'view', 'scope': 'all', 'icon_name': 'file-text', 'sort_order': 21},
        {'code': 'invoices.create', 'name': 'Create Invoices', 'description': 'Generate new invoices', 'category': 'billing', 'resource': 'invoices', 'action': 'create', 'scope': 'all', 'icon_name': 'plus', 'sort_order': 22},
        {'code': 'invoices.update', 'name': 'Update Invoices', 'description': 'Modify invoices', 'category': 'billing', 'resource': 'invoices', 'action': 'update', 'scope': 'all', 'icon_name': 'edit', 'sort_order': 23},
        {'code': 'invoices.delete', 'name': 'Delete Invoices', 'description': 'Remove invoices', 'category': 'billing', 'resource': 'invoices', 'action': 'delete', 'scope': 'all', 'icon_name': 'trash', 'sort_order': 24},
        {'code': 'payments.view', 'name': 'View Payments', 'description': 'View payment records', 'category': 'billing', 'resource': 'payments', 'action': 'view', 'scope': 'all', 'icon_name': 'dollar-sign', 'sort_order': 25},
        {'code': 'payments.create', 'name': 'Process Payments', 'description': 'Record and process payments', 'category': 'billing', 'resource': 'payments', 'action': 'create', 'scope': 'all', 'icon_name': 'credit-card', 'sort_order': 26},
        {'code': 'payments.refund', 'name': 'Process Refunds', 'description': 'Issue payment refunds', 'category': 'billing', 'resource': 'payments', 'action': 'refund', 'scope': 'all', 'icon_name': 'rotate-ccw', 'sort_order': 27},
        
        # Ticket management permissions
        {'code': 'tickets.view', 'name': 'View Tickets', 'description': 'View support tickets', 'category': 'tickets', 'resource': 'tickets', 'action': 'view', 'scope': 'all', 'icon_name': 'help-circle', 'sort_order': 30},
        {'code': 'tickets.create', 'name': 'Create Tickets', 'description': 'Create new support tickets', 'category': 'tickets', 'resource': 'tickets', 'action': 'create', 'scope': 'all', 'icon_name': 'plus', 'sort_order': 31},
        {'code': 'tickets.update', 'name': 'Update Tickets', 'description': 'Modify ticket information', 'category': 'tickets', 'resource': 'tickets', 'action': 'update', 'scope': 'all', 'icon_name': 'edit', 'sort_order': 32},
        {'code': 'tickets.assign', 'name': 'Assign Tickets', 'description': 'Assign tickets to technicians', 'category': 'tickets', 'resource': 'tickets', 'action': 'assign', 'scope': 'all', 'icon_name': 'user-check', 'sort_order': 33},
        {'code': 'tickets.close', 'name': 'Close Tickets', 'description': 'Close and resolve tickets', 'category': 'tickets', 'resource': 'tickets', 'action': 'close', 'scope': 'all', 'icon_name': 'check-circle', 'sort_order': 34},
        
        # Network management permissions
        {'code': 'network.view', 'name': 'View Network', 'description': 'View network infrastructure', 'category': 'network', 'resource': 'network', 'action': 'view', 'scope': 'all', 'icon_name': 'wifi', 'sort_order': 40},
        {'code': 'devices.view', 'name': 'View Devices', 'description': 'View network devices', 'category': 'network', 'resource': 'devices', 'action': 'view', 'scope': 'all', 'icon_name': 'server', 'sort_order': 41},
        {'code': 'devices.configure', 'name': 'Configure Devices', 'description': 'Configure network devices', 'category': 'network', 'resource': 'devices', 'action': 'configure', 'scope': 'all', 'icon_name': 'settings', 'sort_order': 42},
        {'code': 'monitoring.view', 'name': 'View Monitoring', 'description': 'Access monitoring dashboards', 'category': 'network', 'resource': 'monitoring', 'action': 'view', 'scope': 'all', 'icon_name': 'activity', 'sort_order': 43},
        
        # Service management permissions
        {'code': 'services.view', 'name': 'View Services', 'description': 'View service catalog', 'category': 'services', 'resource': 'services', 'action': 'view', 'scope': 'all', 'icon_name': 'layers', 'sort_order': 50},
        {'code': 'services.create', 'name': 'Create Services', 'description': 'Add new services', 'category': 'services', 'resource': 'services', 'action': 'create', 'scope': 'all', 'icon_name': 'plus', 'sort_order': 51},
        {'code': 'services.update', 'name': 'Update Services', 'description': 'Modify service configurations', 'category': 'services', 'resource': 'services', 'action': 'update', 'scope': 'all', 'icon_name': 'edit', 'sort_order': 52},
        {'code': 'service_plans.manage', 'name': 'Manage Service Plans', 'description': 'Create and modify service plans', 'category': 'services', 'resource': 'service_plans', 'action': 'manage', 'scope': 'all', 'icon_name': 'package', 'sort_order': 53},
        
        # Reseller management permissions
        {'code': 'resellers.view', 'name': 'View Resellers', 'description': 'View reseller information', 'category': 'resellers', 'resource': 'resellers', 'action': 'view', 'scope': 'all', 'icon_name': 'users', 'sort_order': 60},
        {'code': 'resellers.create', 'name': 'Create Resellers', 'description': 'Add new resellers', 'category': 'resellers', 'resource': 'resellers', 'action': 'create', 'scope': 'all', 'icon_name': 'user-plus', 'sort_order': 61},
        {'code': 'resellers.update', 'name': 'Update Resellers', 'description': 'Modify reseller information', 'category': 'resellers', 'resource': 'resellers', 'action': 'update', 'scope': 'all', 'icon_name': 'edit', 'sort_order': 62},
        
        # System administration permissions
        {'code': 'admin.users', 'name': 'Manage Users', 'description': 'Manage system users and roles', 'category': 'admin', 'resource': 'users', 'action': 'manage', 'scope': 'all', 'icon_name': 'user-cog', 'sort_order': 70},
        {'code': 'admin.roles', 'name': 'Manage Roles', 'description': 'Create and modify user roles', 'category': 'admin', 'resource': 'roles', 'action': 'manage', 'scope': 'all', 'icon_name': 'shield', 'sort_order': 71},
        {'code': 'admin.permissions', 'name': 'Manage Permissions', 'description': 'Configure system permissions', 'category': 'admin', 'resource': 'permissions', 'action': 'manage', 'scope': 'all', 'icon_name': 'key', 'sort_order': 72},
        {'code': 'admin.settings', 'name': 'System Settings', 'description': 'Configure system settings', 'category': 'admin', 'resource': 'settings', 'action': 'manage', 'scope': 'all', 'icon_name': 'settings', 'sort_order': 73},
        {'code': 'admin.audit', 'name': 'View Audit Logs', 'description': 'Access system audit logs', 'category': 'admin', 'resource': 'audit', 'action': 'view', 'scope': 'all', 'icon_name': 'file-text', 'sort_order': 74},
        
        # Lookup table management permissions
        {'code': 'lookups.manage', 'name': 'Manage Lookup Tables', 'description': 'Configure lookup tables (statuses, types, etc.)', 'category': 'admin', 'resource': 'lookups', 'action': 'manage', 'scope': 'all', 'icon_name': 'list', 'sort_order': 75},
    ]
    
    # Mark all default permissions as system permissions
    for perm in permissions_data:
        perm['is_active'] = True
        perm['is_system'] = True
    
    op.bulk_insert(permissions_table, permissions_data)
    
    # Insert default roles
    roles_table = sa.table('roles',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('is_admin_role', sa.Boolean),
        sa.column('max_users', sa.Integer),
        sa.column('requires_approval', sa.Boolean),
        sa.column('color_hex', sa.String),
        sa.column('icon_name', sa.String)
    )
    
    op.bulk_insert(roles_table, [
        {
            'code': 'super_admin',
            'name': 'Super Administrator',
            'description': 'Full system access with all permissions',
            'is_active': True,
            'is_system': True,
            'sort_order': 1,
            'is_admin_role': True,
            'max_users': None,
            'requires_approval': False,
            'color_hex': '#DC2626',  # Red
            'icon_name': 'crown'
        },
        {
            'code': 'admin',
            'name': 'Administrator',
            'description': 'Administrative access with most permissions',
            'is_active': True,
            'is_system': True,
            'sort_order': 2,
            'is_admin_role': True,
            'max_users': None,
            'requires_approval': True,
            'color_hex': '#7C3AED',  # Purple
            'icon_name': 'shield'
        },
        {
            'code': 'billing_manager',
            'name': 'Billing Manager',
            'description': 'Full access to billing and payment functions',
            'is_active': True,
            'is_system': True,
            'sort_order': 3,
            'is_admin_role': False,
            'max_users': 5,
            'requires_approval': True,
            'color_hex': '#059669',  # Green
            'icon_name': 'credit-card'
        },
        {
            'code': 'customer_support',
            'name': 'Customer Support',
            'description': 'Customer and ticket management access',
            'is_active': True,
            'is_system': True,
            'sort_order': 4,
            'is_admin_role': False,
            'max_users': None,
            'requires_approval': False,
            'color_hex': '#2563EB',  # Blue
            'icon_name': 'headphones'
        },
        {
            'code': 'technician',
            'name': 'Network Technician',
            'description': 'Network and device management access',
            'is_active': True,
            'is_system': True,
            'sort_order': 5,
            'is_admin_role': False,
            'max_users': None,
            'requires_approval': False,
            'color_hex': '#EA580C',  # Orange
            'icon_name': 'wrench'
        },
        {
            'code': 'sales_manager',
            'name': 'Sales Manager',
            'description': 'Customer and reseller management access',
            'is_active': True,
            'is_system': True,
            'sort_order': 6,
            'is_admin_role': False,
            'max_users': 10,
            'requires_approval': True,
            'color_hex': '#7C2D12',  # Brown
            'icon_name': 'trending-up'
        },
        {
            'code': 'read_only',
            'name': 'Read Only User',
            'description': 'View-only access to most system areas',
            'is_active': True,
            'is_system': True,
            'sort_order': 7,
            'is_admin_role': False,
            'max_users': None,
            'requires_approval': False,
            'color_hex': '#6B7280',  # Gray
            'icon_name': 'eye'
        }
    ])


def downgrade():
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')
