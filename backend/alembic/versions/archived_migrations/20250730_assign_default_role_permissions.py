"""Assign default permissions to system roles

Revision ID: 20250730_assign_default_role_permissions
Revises: 20250730_create_rbac_system
Create Date: 2025-07-30 08:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250730_assign_default_role_permissions'
down_revision = '20250730_create_rbac_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create helper tables for bulk operations
    role_permissions_table = sa.table('role_permissions',
        sa.column('role_id', sa.Integer),
        sa.column('permission_id', sa.Integer)
    )
    
    # Define role-permission mappings
    # Super Admin gets ALL permissions
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'super_admin' AND p.is_active = true
    """)
    
    # Admin gets most permissions (excluding some super admin functions)
    admin_excluded_permissions = [
        'admin.users', 'admin.roles', 'admin.permissions'
    ]
    excluded_list = "'" + "', '".join(admin_excluded_permissions) + "'"
    
    op.execute(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'admin' 
        AND p.is_active = true 
        AND p.code NOT IN ({excluded_list})
    """)
    
    # Billing Manager - billing and customer permissions
    billing_permissions = [
        'dashboard.view', 'dashboard.analytics',
        'customers.view', 'customers.create', 'customers.update', 'customers.export',
        'billing.view', 'invoices.view', 'invoices.create', 'invoices.update', 'invoices.delete',
        'payments.view', 'payments.create', 'payments.refund',
        'services.view', 'service_plans.manage'
    ]
    billing_list = "'" + "', '".join(billing_permissions) + "'"
    
    op.execute(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'billing_manager' 
        AND p.code IN ({billing_list})
    """)
    
    # Customer Support - customer and ticket permissions
    support_permissions = [
        'dashboard.view',
        'customers.view', 'customers.create', 'customers.update',
        'tickets.view', 'tickets.create', 'tickets.update', 'tickets.assign', 'tickets.close',
        'services.view'
    ]
    support_list = "'" + "', '".join(support_permissions) + "'"
    
    op.execute(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'customer_support' 
        AND p.code IN ({support_list})
    """)
    
    # Technician - network and device permissions
    tech_permissions = [
        'dashboard.view',
        'customers.view',
        'tickets.view', 'tickets.update', 'tickets.close',
        'network.view', 'devices.view', 'devices.configure', 'monitoring.view',
        'services.view'
    ]
    tech_list = "'" + "', '".join(tech_permissions) + "'"
    
    op.execute(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'technician' 
        AND p.code IN ({tech_list})
    """)
    
    # Sales Manager - customer and reseller permissions
    sales_permissions = [
        'dashboard.view', 'dashboard.analytics',
        'customers.view', 'customers.create', 'customers.update', 'customers.export',
        'resellers.view', 'resellers.create', 'resellers.update',
        'services.view', 'service_plans.manage'
    ]
    sales_list = "'" + "', '".join(sales_permissions) + "'"
    
    op.execute(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'sales_manager' 
        AND p.code IN ({sales_list})
    """)
    
    # Read Only User - view permissions only
    readonly_permissions = [
        'dashboard.view', 'dashboard.analytics',
        'customers.view', 'billing.view', 'invoices.view', 'payments.view',
        'tickets.view', 'network.view', 'devices.view', 'monitoring.view',
        'services.view', 'resellers.view'
    ]
    readonly_list = "'" + "', '".join(readonly_permissions) + "'"
    
    op.execute(f"""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'read_only' 
        AND p.code IN ({readonly_list})
    """)


def downgrade():
    # Remove all role-permission assignments
    op.execute("DELETE FROM role_permissions")
