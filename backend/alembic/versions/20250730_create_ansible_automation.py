"""Create Ansible automation system

Revision ID: 20250730_create_ansible_automation
Revises: 20250730_create_ipoe_authentication
Create Date: 2025-07-30 09:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_ansible_automation'
down_revision = '20250730_create_ipoe_authentication'
branch_labels = None
depends_on = None


def upgrade():
    # Create automation_sites table
    op.create_table('automation_sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('latitude', sa.DECIMAL(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.DECIMAL(precision=11, scale=8), nullable=True),
        sa.Column('site_type', sa.String(length=50), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=True),
        sa.Column('contact_person', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('power_type', sa.String(length=50), nullable=True),
        sa.Column('connectivity_type', sa.String(length=50), nullable=True),
        sa.Column('rack_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('monitoring_enabled', sa.Boolean(), nullable=True),
        sa.Column('last_maintenance', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_maintenance', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_sites_id'), 'automation_sites', ['id'], unique=False)
    op.create_index(op.f('ix_automation_sites_name'), 'automation_sites', ['name'], unique=True)
    op.create_index(op.f('ix_automation_sites_code'), 'automation_sites', ['code'], unique=True)

    # Create automation_devices table
    op.create_table('automation_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('vendor', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('management_ip', sa.String(length=45), nullable=False),
        sa.Column('management_port', sa.Integer(), nullable=True),
        sa.Column('management_protocol', sa.String(length=20), nullable=True),
        sa.Column('site_id', sa.Integer(), nullable=False),
        sa.Column('rack_position', sa.String(length=50), nullable=True),
        sa.Column('physical_location', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_managed', sa.Boolean(), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('os_version', sa.String(length=100), nullable=True),
        sa.Column('firmware_version', sa.String(length=100), nullable=True),
        sa.Column('config_version', sa.String(length=100), nullable=True),
        sa.Column('last_backup', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ansible_host_group', sa.String(length=100), nullable=True),
        sa.Column('ansible_variables', sa.JSON(), nullable=True),
        sa.Column('playbook_tags', sa.JSON(), nullable=True),
        sa.Column('cpu_usage_percent', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('memory_usage_percent', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('uptime_days', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['automation_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_devices_id'), 'automation_devices', ['id'], unique=False)
    op.create_index(op.f('ix_automation_devices_hostname'), 'automation_devices', ['hostname'], unique=True)
    op.create_index(op.f('ix_automation_devices_management_ip'), 'automation_devices', ['management_ip'], unique=False)
    op.create_index(op.f('ix_automation_devices_site_id'), 'automation_devices', ['site_id'], unique=False)
    op.create_index(op.f('ix_automation_devices_serial_number'), 'automation_devices', ['serial_number'], unique=True)
    op.create_index('idx_device_site_type', 'automation_devices', ['site_id', 'device_type'], unique=False)
    op.create_index('idx_device_vendor_model', 'automation_devices', ['vendor', 'model'], unique=False)
    op.create_index('idx_device_status', 'automation_devices', ['status'], unique=False)

    # Create automation_device_credentials table
    op.create_table('automation_device_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.Integer(), nullable=False),
        sa.Column('credential_type', sa.String(length=20), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('password_encrypted', sa.Text(), nullable=True),
        sa.Column('private_key_encrypted', sa.Text(), nullable=True),
        sa.Column('snmp_community', sa.String(length=255), nullable=True),
        sa.Column('snmp_version', sa.String(length=10), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('api_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_validated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('encryption_key_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['automation_devices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_device_credentials_id'), 'automation_device_credentials', ['id'], unique=False)
    op.create_index(op.f('ix_automation_device_credentials_device_id'), 'automation_device_credentials', ['device_id'], unique=False)

    # Create automation_provisioning_tasks table
    op.create_table('automation_provisioning_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('device_id', sa.Integer(), nullable=True),
        sa.Column('site_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('playbook_name', sa.String(length=255), nullable=False),
        sa.Column('playbook_tags', sa.JSON(), nullable=True),
        sa.Column('ansible_variables', sa.JSON(), nullable=True),
        sa.Column('inventory_groups', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('stdout_log', sa.Text(), nullable=True),
        sa.Column('stderr_log', sa.Text(), nullable=True),
        sa.Column('ansible_facts', sa.JSON(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('depends_on_task_id', sa.Integer(), nullable=True),
        sa.Column('executed_by', sa.Integer(), nullable=True),
        sa.Column('execution_node', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['depends_on_task_id'], ['automation_provisioning_tasks.id'], ),
        sa.ForeignKeyConstraint(['device_id'], ['automation_devices.id'], ),
        sa.ForeignKeyConstraint(['executed_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['customer_services.id'], ),
        sa.ForeignKeyConstraint(['site_id'], ['automation_sites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_provisioning_tasks_id'), 'automation_provisioning_tasks', ['id'], unique=False)
    op.create_index('idx_task_status_priority', 'automation_provisioning_tasks', ['status', 'priority'], unique=False)
    op.create_index('idx_task_device_status', 'automation_provisioning_tasks', ['device_id', 'status'], unique=False)
    op.create_index('idx_task_scheduled_at', 'automation_provisioning_tasks', ['scheduled_at'], unique=False)
    op.create_index('idx_task_type_category', 'automation_provisioning_tasks', ['task_type', 'category'], unique=False)

    # Create automation_ansible_playbooks table
    op.create_table('automation_ansible_playbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('device_types', sa.JSON(), nullable=True),
        sa.Column('vendors', sa.JSON(), nullable=True),
        sa.Column('default_variables', sa.JSON(), nullable=True),
        sa.Column('required_variables', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_tested', sa.Boolean(), nullable=True),
        sa.Column('test_results', sa.JSON(), nullable=True),
        sa.Column('last_tested', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_production_ready', sa.Boolean(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_automation_ansible_playbooks_id'), 'automation_ansible_playbooks', ['id'], unique=False)
    op.create_index(op.f('ix_automation_ansible_playbooks_name'), 'automation_ansible_playbooks', ['name'], unique=True)

    # Set default values for new tables
    op.execute("UPDATE automation_sites SET rack_count = 0 WHERE rack_count IS NULL")
    op.execute("UPDATE automation_sites SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE automation_sites SET monitoring_enabled = true WHERE monitoring_enabled IS NULL")

    op.execute("UPDATE automation_devices SET management_port = 22 WHERE management_port IS NULL")
    op.execute("UPDATE automation_devices SET management_protocol = 'ssh' WHERE management_protocol IS NULL")
    op.execute("UPDATE automation_devices SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE automation_devices SET is_managed = true WHERE is_managed IS NULL")
    op.execute("UPDATE automation_devices SET ansible_variables = '{}' WHERE ansible_variables IS NULL")
    op.execute("UPDATE automation_devices SET playbook_tags = '[]' WHERE playbook_tags IS NULL")

    op.execute("UPDATE automation_device_credentials SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE automation_device_credentials SET validation_status = 'pending' WHERE validation_status IS NULL")

    op.execute("UPDATE automation_provisioning_tasks SET priority = 'medium' WHERE priority IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET status = 'pending' WHERE status IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET playbook_tags = '[]' WHERE playbook_tags IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET ansible_variables = '{}' WHERE ansible_variables IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET inventory_groups = '[]' WHERE inventory_groups IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET max_retries = 3 WHERE max_retries IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET retry_count = 0 WHERE retry_count IS NULL")
    op.execute("UPDATE automation_provisioning_tasks SET ansible_facts = '{}' WHERE ansible_facts IS NULL")

    op.execute("UPDATE automation_ansible_playbooks SET version = '1.0' WHERE version IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET device_types = '[]' WHERE device_types IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET vendors = '[]' WHERE vendors IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET default_variables = '{}' WHERE default_variables IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET required_variables = '[]' WHERE required_variables IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET tags = '[]' WHERE tags IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET is_tested = false WHERE is_tested IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET test_results = '{}' WHERE test_results IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE automation_ansible_playbooks SET is_production_ready = false WHERE is_production_ready IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('automation_sites', 'rack_count', nullable=False)
    op.alter_column('automation_sites', 'is_active', nullable=False)
    op.alter_column('automation_sites', 'monitoring_enabled', nullable=False)

    op.alter_column('automation_devices', 'management_port', nullable=False)
    op.alter_column('automation_devices', 'management_protocol', nullable=False)
    op.alter_column('automation_devices', 'is_managed', nullable=False)
    op.alter_column('automation_devices', 'ansible_variables', nullable=False)
    op.alter_column('automation_devices', 'playbook_tags', nullable=False)

    op.alter_column('automation_device_credentials', 'is_active', nullable=False)
    op.alter_column('automation_device_credentials', 'validation_status', nullable=False)

    op.alter_column('automation_provisioning_tasks', 'priority', nullable=False)
    op.alter_column('automation_provisioning_tasks', 'playbook_tags', nullable=False)
    op.alter_column('automation_provisioning_tasks', 'ansible_variables', nullable=False)
    op.alter_column('automation_provisioning_tasks', 'inventory_groups', nullable=False)
    op.alter_column('automation_provisioning_tasks', 'max_retries', nullable=False)
    op.alter_column('automation_provisioning_tasks', 'retry_count', nullable=False)
    op.alter_column('automation_provisioning_tasks', 'ansible_facts', nullable=False)

    op.alter_column('automation_ansible_playbooks', 'version', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'device_types', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'vendors', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'default_variables', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'required_variables', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'tags', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'is_tested', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'test_results', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'is_active', nullable=False)
    op.alter_column('automation_ansible_playbooks', 'is_production_ready', nullable=False)

    # Add RBAC permissions for automation management
    op.execute("""
        INSERT INTO permissions (code, name, description, resource, action, category, is_system, created_at)
        VALUES 
        ('automation.view', 'View Automation', 'View automation dashboard and status', 'automation', 'view', 'automation', true, NOW()),
        ('automation.sites.view', 'View Sites', 'View automation sites', 'automation_sites', 'view', 'automation', true, NOW()),
        ('automation.sites.create', 'Create Sites', 'Create automation sites', 'automation_sites', 'create', 'automation', true, NOW()),
        ('automation.sites.update', 'Update Sites', 'Modify automation sites', 'automation_sites', 'update', 'automation', true, NOW()),
        ('automation.sites.delete', 'Delete Sites', 'Remove automation sites', 'automation_sites', 'delete', 'automation', true, NOW()),
        ('automation.devices.view', 'View Devices', 'View automation devices', 'automation_devices', 'view', 'automation', true, NOW()),
        ('automation.devices.create', 'Create Devices', 'Create automation devices', 'automation_devices', 'create', 'automation', true, NOW()),
        ('automation.devices.update', 'Update Devices', 'Modify automation devices', 'automation_devices', 'update', 'automation', true, NOW()),
        ('automation.devices.delete', 'Delete Devices', 'Remove automation devices', 'automation_devices', 'delete', 'automation', true, NOW()),
        ('automation.tasks.view', 'View Tasks', 'View provisioning tasks', 'automation_tasks', 'view', 'automation', true, NOW()),
        ('automation.tasks.create', 'Create Tasks', 'Create provisioning tasks', 'automation_tasks', 'create', 'automation', true, NOW()),
        ('automation.tasks.execute', 'Execute Tasks', 'Execute provisioning tasks', 'automation_tasks', 'execute', 'automation', true, NOW()),
        ('automation.tasks.cancel', 'Cancel Tasks', 'Cancel provisioning tasks', 'automation_tasks', 'cancel', 'automation', true, NOW()),
        ('automation.provision', 'Provision Services', 'Provision customer services', 'automation', 'provision', 'automation', true, NOW()),
        ('automation.backup', 'Backup Configs', 'Backup device configurations', 'automation', 'backup', 'automation', true, NOW()),
        ('automation.playbooks.view', 'View Playbooks', 'View Ansible playbooks', 'automation_playbooks', 'view', 'automation', true, NOW()),
        ('automation.playbooks.create', 'Create Playbooks', 'Create Ansible playbooks', 'automation_playbooks', 'create', 'automation', true, NOW()),
        ('automation.playbooks.update', 'Update Playbooks', 'Modify Ansible playbooks', 'automation_playbooks', 'update', 'automation', true, NOW()),
        ('automation.playbooks.delete', 'Delete Playbooks', 'Remove Ansible playbooks', 'automation_playbooks', 'delete', 'automation', true, NOW())
        ON CONFLICT (code) DO NOTHING;
    """)

    # Assign automation permissions to relevant roles
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code IN ('super_admin', 'admin') 
        AND p.code LIKE 'automation.%'
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Assign limited automation permissions to technician
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'technician'
        AND p.code IN ('automation.view', 'automation.sites.view', 'automation.devices.view', 'automation.devices.update',
                       'automation.tasks.view', 'automation.tasks.create', 'automation.tasks.execute', 
                       'automation.provision', 'automation.backup', 'automation.playbooks.view')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Assign read-only automation permissions to other roles
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code IN ('customer_support', 'read_only')
        AND p.code IN ('automation.view', 'automation.sites.view', 'automation.devices.view', 'automation.tasks.view')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Create sample sites and playbooks
    op.execute("""
        INSERT INTO automation_sites (name, code, description, site_type, is_active, monitoring_enabled, rack_count)
        VALUES 
        ('Main Data Center', 'DC01', 'Primary data center facility', 'datacenter', true, true, 20),
        ('POP Site Alpha', 'POP01', 'Point of presence site Alpha', 'pop', true, true, 5),
        ('Tower Site Beta', 'TWR01', 'Wireless tower site Beta', 'tower', true, true, 2)
        ON CONFLICT (name) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO automation_ansible_playbooks (name, description, file_path, category, device_types, vendors, is_active, is_production_ready)
        VALUES 
        ('provision_internet_service.yml', 'Provision internet service for customers', '/opt/isp-framework/ansible/playbooks/provision_internet_service.yml', 'provisioning', '["router", "switch"]', '["mikrotik", "cisco"]', true, true),
        ('backup_config.yml', 'Backup device configurations', '/opt/isp-framework/ansible/playbooks/backup_config.yml', 'maintenance', '["router", "switch", "olt"]', '["mikrotik", "cisco", "huawei", "zte"]', true, true),
        ('update_monitoring.yml', 'Update device monitoring configuration', '/opt/isp-framework/ansible/playbooks/update_monitoring.yml', 'monitoring', '["router", "switch", "olt", "ap"]', '["mikrotik", "cisco", "huawei", "zte", "ubiquiti"]', true, true),
        ('provision_voice_service.yml', 'Provision voice service for customers', '/opt/isp-framework/ansible/playbooks/provision_voice_service.yml', 'provisioning', '["router", "switch"]', '["mikrotik", "cisco"]', true, false),
        ('firmware_update.yml', 'Update device firmware', '/opt/isp-framework/ansible/playbooks/firmware_update.yml', 'maintenance', '["router", "switch", "ap"]', '["mikrotik", "ubiquiti"]', true, false)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade():
    # Remove RBAC permissions
    op.execute("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code LIKE 'automation.%')")
    op.execute("DELETE FROM permissions WHERE code LIKE 'automation.%'")

    # Drop automation tables in reverse order
    op.drop_index(op.f('ix_automation_ansible_playbooks_name'), table_name='automation_ansible_playbooks')
    op.drop_index(op.f('ix_automation_ansible_playbooks_id'), table_name='automation_ansible_playbooks')
    op.drop_table('automation_ansible_playbooks')
    
    op.drop_index('idx_task_type_category', table_name='automation_provisioning_tasks')
    op.drop_index('idx_task_scheduled_at', table_name='automation_provisioning_tasks')
    op.drop_index('idx_task_device_status', table_name='automation_provisioning_tasks')
    op.drop_index('idx_task_status_priority', table_name='automation_provisioning_tasks')
    op.drop_index(op.f('ix_automation_provisioning_tasks_id'), table_name='automation_provisioning_tasks')
    op.drop_table('automation_provisioning_tasks')
    
    op.drop_index(op.f('ix_automation_device_credentials_device_id'), table_name='automation_device_credentials')
    op.drop_index(op.f('ix_automation_device_credentials_id'), table_name='automation_device_credentials')
    op.drop_table('automation_device_credentials')
    
    op.drop_index('idx_device_status', table_name='automation_devices')
    op.drop_index('idx_device_vendor_model', table_name='automation_devices')
    op.drop_index('idx_device_site_type', table_name='automation_devices')
    op.drop_index(op.f('ix_automation_devices_serial_number'), table_name='automation_devices')
    op.drop_index(op.f('ix_automation_devices_site_id'), table_name='automation_devices')
    op.drop_index(op.f('ix_automation_devices_management_ip'), table_name='automation_devices')
    op.drop_index(op.f('ix_automation_devices_hostname'), table_name='automation_devices')
    op.drop_index(op.f('ix_automation_devices_id'), table_name='automation_devices')
    op.drop_table('automation_devices')
    
    op.drop_index(op.f('ix_automation_sites_code'), table_name='automation_sites')
    op.drop_index(op.f('ix_automation_sites_name'), table_name='automation_sites')
    op.drop_index(op.f('ix_automation_sites_id'), table_name='automation_sites')
    op.drop_table('automation_sites')
