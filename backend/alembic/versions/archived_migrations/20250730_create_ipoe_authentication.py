"""Create IPoE authentication system

Revision ID: 20250730_create_ipoe_authentication
Revises: 20250730_create_mac_authentication
Create Date: 2025-07-30 08:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_ipoe_authentication'
down_revision = '20250730_create_mac_authentication'
branch_labels = None
depends_on = None


def upgrade():
    # Create olt_profiles table
    op.create_table('olt_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('olt_type', sa.String(length=50), nullable=False),
        sa.Column('management_ip', sa.String(length=45), nullable=False),
        sa.Column('snmp_community', sa.String(length=100), nullable=True),
        sa.Column('snmp_version', sa.String(length=10), nullable=True),
        sa.Column('default_vlan_id', sa.Integer(), nullable=True),
        sa.Column('vlan_range_start', sa.Integer(), nullable=True),
        sa.Column('vlan_range_end', sa.Integer(), nullable=True),
        sa.Column('speed_profiles', sa.JSON(), nullable=True),
        sa.Column('radius_nas_identifier', sa.String(length=255), nullable=True),
        sa.Column('radius_nas_ip', sa.String(length=45), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_olt_profiles_id'), 'olt_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_olt_profiles_name'), 'olt_profiles', ['name'], unique=True)

    # Create access_circuits table
    op.create_table('access_circuits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('circuit_id', sa.String(length=255), nullable=False),
        sa.Column('olt_profile_id', sa.Integer(), nullable=False),
        sa.Column('pon_port', sa.String(length=50), nullable=True),
        sa.Column('onu_id', sa.Integer(), nullable=True),
        sa.Column('onu_serial', sa.String(length=100), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('vlan_id', sa.Integer(), nullable=True),
        sa.Column('inner_vlan_id', sa.Integer(), nullable=True),
        sa.Column('mac_address', sa.String(length=17), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('latitude', sa.String(length=20), nullable=True),
        sa.Column('longitude', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('provision_status', sa.String(length=20), nullable=True),
        sa.Column('fiber_length_meters', sa.Integer(), nullable=True),
        sa.Column('signal_level_dbm', sa.String(length=10), nullable=True),
        sa.Column('last_signal_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('agent_circuit_id', sa.String(length=255), nullable=True),
        sa.Column('agent_remote_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['olt_profile_id'], ['olt_profiles.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['customer_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_access_circuits_id'), 'access_circuits', ['id'], unique=False)
    op.create_index(op.f('ix_access_circuits_circuit_id'), 'access_circuits', ['circuit_id'], unique=True)
    op.create_index('idx_circuit_customer_status', 'access_circuits', ['customer_id', 'status'], unique=False)
    op.create_index('idx_circuit_onu_serial', 'access_circuits', ['onu_serial'], unique=False)
    op.create_index('idx_circuit_agent_circuit_id', 'access_circuits', ['agent_circuit_id'], unique=False)
    op.create_index('idx_circuit_status', 'access_circuits', ['status'], unique=False)
    op.create_index(op.f('ix_access_circuits_customer_id'), 'access_circuits', ['customer_id'], unique=False)
    op.create_index(op.f('ix_access_circuits_service_id'), 'access_circuits', ['service_id'], unique=False)
    op.create_index(op.f('ix_access_circuits_mac_address'), 'access_circuits', ['mac_address'], unique=False)

    # Create ipoe_sessions table
    op.create_table('ipoe_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('circuit_id', sa.String(length=255), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('client_mac', sa.String(length=17), nullable=True),
        sa.Column('nas_identifier', sa.String(length=255), nullable=True),
        sa.Column('nas_port', sa.String(length=50), nullable=True),
        sa.Column('agent_circuit_id', sa.String(length=255), nullable=True),
        sa.Column('agent_remote_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('download_speed_kbps', sa.Integer(), nullable=True),
        sa.Column('upload_speed_kbps', sa.Integer(), nullable=True),
        sa.Column('session_timeout', sa.Integer(), nullable=True),
        sa.Column('bytes_in', sa.Integer(), nullable=True),
        sa.Column('bytes_out', sa.Integer(), nullable=True),
        sa.Column('packets_in', sa.Integer(), nullable=True),
        sa.Column('packets_out', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_update', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['circuit_id'], ['access_circuits.circuit_id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['customer_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ipoe_sessions_id'), 'ipoe_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_ipoe_sessions_session_id'), 'ipoe_sessions', ['session_id'], unique=True)
    op.create_index('idx_session_customer_status', 'ipoe_sessions', ['customer_id', 'status'], unique=False)
    op.create_index('idx_session_circuit_status', 'ipoe_sessions', ['circuit_id', 'status'], unique=False)
    op.create_index('idx_session_start_time', 'ipoe_sessions', ['start_time'], unique=False)
    op.create_index('idx_session_client_ip', 'ipoe_sessions', ['client_ip'], unique=False)
    op.create_index(op.f('ix_ipoe_sessions_circuit_id'), 'ipoe_sessions', ['circuit_id'], unique=False)
    op.create_index(op.f('ix_ipoe_sessions_customer_id'), 'ipoe_sessions', ['customer_id'], unique=False)
    op.create_index(op.f('ix_ipoe_sessions_service_id'), 'ipoe_sessions', ['service_id'], unique=False)
    op.create_index(op.f('ix_ipoe_sessions_client_mac'), 'ipoe_sessions', ['client_mac'], unique=False)

    # Create dhcp_relays table
    op.create_table('dhcp_relays',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('relay_ip', sa.String(length=45), nullable=False),
        sa.Column('dhcp_server_ip', sa.String(length=45), nullable=False),
        sa.Column('radius_server_ip', sa.String(length=45), nullable=False),
        sa.Column('enable_option82', sa.Boolean(), nullable=True),
        sa.Column('circuit_id_format', sa.String(length=255), nullable=True),
        sa.Column('remote_id_format', sa.String(length=255), nullable=True),
        sa.Column('radius_nas_identifier', sa.String(length=255), nullable=True),
        sa.Column('radius_secret', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dhcp_relays_id'), 'dhcp_relays', ['id'], unique=False)
    op.create_index(op.f('ix_dhcp_relays_name'), 'dhcp_relays', ['name'], unique=True)

    # Add IPoE authentication columns to customer_services table
    op.add_column('customer_services', sa.Column('ipoe_auth_enabled', sa.Boolean(), nullable=True))
    op.add_column('customer_services', sa.Column('access_circuit_id', sa.String(length=255), nullable=True))
    op.add_column('customer_services', sa.Column('onu_serial', sa.String(length=100), nullable=True))

    # Set default values for existing services
    op.execute("UPDATE customer_services SET ipoe_auth_enabled = false WHERE ipoe_auth_enabled IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('customer_services', 'ipoe_auth_enabled', nullable=False)

    # Set default values for new tables
    op.execute("UPDATE olt_profiles SET snmp_version = '2c' WHERE snmp_version IS NULL")
    op.execute("UPDATE olt_profiles SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE access_circuits SET status = 'available' WHERE status IS NULL")
    op.execute("UPDATE access_circuits SET provision_status = 'pending' WHERE provision_status IS NULL")
    op.execute("UPDATE ipoe_sessions SET status = 'active' WHERE status IS NULL")
    op.execute("UPDATE ipoe_sessions SET bytes_in = 0 WHERE bytes_in IS NULL")
    op.execute("UPDATE ipoe_sessions SET bytes_out = 0 WHERE bytes_out IS NULL")
    op.execute("UPDATE ipoe_sessions SET packets_in = 0 WHERE packets_in IS NULL")
    op.execute("UPDATE ipoe_sessions SET packets_out = 0 WHERE packets_out IS NULL")
    op.execute("UPDATE dhcp_relays SET enable_option82 = true WHERE enable_option82 IS NULL")
    op.execute("UPDATE dhcp_relays SET circuit_id_format = '{olt_ip}:{pon_port}:{onu_id}' WHERE circuit_id_format IS NULL")
    op.execute("UPDATE dhcp_relays SET remote_id_format = '{onu_serial}' WHERE remote_id_format IS NULL")
    op.execute("UPDATE dhcp_relays SET is_active = true WHERE is_active IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('olt_profiles', 'snmp_version', nullable=False)
    op.alter_column('olt_profiles', 'is_active', nullable=False)
    op.alter_column('access_circuits', 'provision_status', nullable=False)
    op.alter_column('ipoe_sessions', 'bytes_in', nullable=False)
    op.alter_column('ipoe_sessions', 'bytes_out', nullable=False)
    op.alter_column('ipoe_sessions', 'packets_in', nullable=False)
    op.alter_column('ipoe_sessions', 'packets_out', nullable=False)
    op.alter_column('dhcp_relays', 'enable_option82', nullable=False)
    op.alter_column('dhcp_relays', 'circuit_id_format', nullable=False)
    op.alter_column('dhcp_relays', 'remote_id_format', nullable=False)
    op.alter_column('dhcp_relays', 'is_active', nullable=False)

    # Add RBAC permissions for IPoE management
    op.execute("""
        INSERT INTO permissions (code, name, description, resource, action, category, is_system, created_at)
        VALUES 
        ('ipoe.view', 'View IPoE', 'View IPoE circuits and sessions', 'ipoe', 'view', 'networking', true, NOW()),
        ('ipoe.create', 'Create IPoE', 'Create IPoE circuits and configurations', 'ipoe', 'create', 'networking', true, NOW()),
        ('ipoe.update', 'Update IPoE', 'Modify IPoE circuits and settings', 'ipoe', 'update', 'networking', true, NOW()),
        ('ipoe.delete', 'Delete IPoE', 'Remove IPoE circuits and configurations', 'ipoe', 'delete', 'networking', true, NOW()),
        ('ipoe.assign', 'Assign IPoE', 'Assign circuits to customers', 'ipoe', 'assign', 'networking', true, NOW()),
        ('ipoe.provision', 'Provision IPoE', 'Provision and activate circuits', 'ipoe', 'provision', 'networking', true, NOW()),
        ('olt_profiles.view', 'View OLT Profiles', 'View OLT configuration profiles', 'olt_profiles', 'view', 'networking', true, NOW()),
        ('olt_profiles.create', 'Create OLT Profiles', 'Create OLT configuration profiles', 'olt_profiles', 'create', 'networking', true, NOW()),
        ('olt_profiles.update', 'Update OLT Profiles', 'Modify OLT configuration profiles', 'olt_profiles', 'update', 'networking', true, NOW()),
        ('olt_profiles.delete', 'Delete OLT Profiles', 'Remove OLT configuration profiles', 'olt_profiles', 'delete', 'networking', true, NOW()),
        ('dhcp_relays.view', 'View DHCP Relays', 'View DHCP relay configurations', 'dhcp_relays', 'view', 'networking', true, NOW()),
        ('dhcp_relays.create', 'Create DHCP Relays', 'Create DHCP relay configurations', 'dhcp_relays', 'create', 'networking', true, NOW()),
        ('dhcp_relays.update', 'Update DHCP Relays', 'Modify DHCP relay configurations', 'dhcp_relays', 'update', 'networking', true, NOW()),
        ('dhcp_relays.delete', 'Delete DHCP Relays', 'Remove DHCP relay configurations', 'dhcp_relays', 'delete', 'networking', true, NOW())
        ON CONFLICT (code) DO NOTHING;
    """)

    # Assign IPoE permissions to relevant roles
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code IN ('super_admin', 'admin', 'technician') 
        AND p.code IN ('ipoe.view', 'ipoe.create', 'ipoe.update', 'ipoe.delete', 'ipoe.assign', 'ipoe.provision',
                       'olt_profiles.view', 'olt_profiles.create', 'olt_profiles.update', 'olt_profiles.delete',
                       'dhcp_relays.view', 'dhcp_relays.create', 'dhcp_relays.update', 'dhcp_relays.delete')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Assign limited IPoE permissions to customer support
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'customer_support'
        AND p.code IN ('ipoe.view', 'ipoe.assign')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Assign read-only IPoE permissions to read_only role
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.code = 'read_only'
        AND p.code IN ('ipoe.view', 'olt_profiles.view', 'dhcp_relays.view')
        ON CONFLICT (role_id, permission_id) DO NOTHING;
    """)

    # Create sample OLT profiles for common vendors
    op.execute("""
        INSERT INTO olt_profiles (name, description, olt_type, management_ip, snmp_community, snmp_version, 
                                 default_vlan_id, vlan_range_start, vlan_range_end, speed_profiles, is_active)
        VALUES 
        ('Huawei MA5800', 'Huawei MA5800 series OLT', 'huawei', '192.168.1.100', 'public', '2c', 
         100, 100, 4000, '{"100M": {"down": 100000, "up": 50000}, "200M": {"down": 200000, "up": 100000}}', true),
        ('ZTE C320', 'ZTE C320 series OLT', 'zte', '192.168.1.101', 'public', '2c', 
         200, 200, 4000, '{"100M": {"down": 100000, "up": 50000}, "200M": {"down": 200000, "up": 100000}}', true),
        ('Nokia ISAM', 'Nokia ISAM series OLT', 'nokia', '192.168.1.102', 'public', '2c', 
         300, 300, 4000, '{"100M": {"down": 100000, "up": 50000}, "200M": {"down": 200000, "up": 100000}}', true)
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade():
    # Remove RBAC permissions
    op.execute("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE code LIKE 'ipoe.%' OR code LIKE 'olt_profiles.%' OR code LIKE 'dhcp_relays.%')")
    op.execute("DELETE FROM permissions WHERE code LIKE 'ipoe.%' OR code LIKE 'olt_profiles.%' OR code LIKE 'dhcp_relays.%'")

    # Remove IPoE authentication columns from customer_services
    op.drop_column('customer_services', 'onu_serial')
    op.drop_column('customer_services', 'access_circuit_id')
    op.drop_column('customer_services', 'ipoe_auth_enabled')

    # Drop IPoE tables
    op.drop_index(op.f('ix_dhcp_relays_name'), table_name='dhcp_relays')
    op.drop_index(op.f('ix_dhcp_relays_id'), table_name='dhcp_relays')
    op.drop_table('dhcp_relays')
    
    op.drop_index(op.f('ix_ipoe_sessions_client_mac'), table_name='ipoe_sessions')
    op.drop_index(op.f('ix_ipoe_sessions_service_id'), table_name='ipoe_sessions')
    op.drop_index(op.f('ix_ipoe_sessions_customer_id'), table_name='ipoe_sessions')
    op.drop_index(op.f('ix_ipoe_sessions_circuit_id'), table_name='ipoe_sessions')
    op.drop_index('idx_session_client_ip', table_name='ipoe_sessions')
    op.drop_index('idx_session_start_time', table_name='ipoe_sessions')
    op.drop_index('idx_session_circuit_status', table_name='ipoe_sessions')
    op.drop_index('idx_session_customer_status', table_name='ipoe_sessions')
    op.drop_index(op.f('ix_ipoe_sessions_session_id'), table_name='ipoe_sessions')
    op.drop_index(op.f('ix_ipoe_sessions_id'), table_name='ipoe_sessions')
    op.drop_table('ipoe_sessions')
    
    op.drop_index(op.f('ix_access_circuits_mac_address'), table_name='access_circuits')
    op.drop_index(op.f('ix_access_circuits_service_id'), table_name='access_circuits')
    op.drop_index(op.f('ix_access_circuits_customer_id'), table_name='access_circuits')
    op.drop_index('idx_circuit_status', table_name='access_circuits')
    op.drop_index('idx_circuit_agent_circuit_id', table_name='access_circuits')
    op.drop_index('idx_circuit_onu_serial', table_name='access_circuits')
    op.drop_index('idx_circuit_customer_status', table_name='access_circuits')
    op.drop_index(op.f('ix_access_circuits_circuit_id'), table_name='access_circuits')
    op.drop_index(op.f('ix_access_circuits_id'), table_name='access_circuits')
    op.drop_table('access_circuits')
    
    op.drop_index(op.f('ix_olt_profiles_name'), table_name='olt_profiles')
    op.drop_index(op.f('ix_olt_profiles_id'), table_name='olt_profiles')
    op.drop_table('olt_profiles')
