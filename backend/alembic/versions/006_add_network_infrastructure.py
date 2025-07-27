"""Add network infrastructure tables

Revision ID: 006_add_network_infrastructure
Revises: 005_add_portal_id_uniqueness
Create Date: 2025-07-23 22:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_network_infrastructure'
down_revision = '005a_add_locations_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create network_sites table
    op.create_table('network_sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('gps', sa.String(length=100), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('partners_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_network_sites_id'), 'network_sites', ['id'], unique=False)

    # Create network_categories table
    op.create_table('network_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_network_categories_id'), 'network_categories', ['id'], unique=False)

    # Create ipv4_networks table
    op.create_table('ipv4_networks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', postgresql.INET(), nullable=False),
        sa.Column('mask', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('network_category_id', sa.Integer(), nullable=False),
        sa.Column('network_type', sa.String(length=20), nullable=True),
        sa.Column('type_of_usage', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['network_category_id'], ['network_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ipv4_networks_id'), 'ipv4_networks', ['id'], unique=False)

    # Create ipv4_ips table
    op.create_table('ipv4_ips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ipv4_networks_id', sa.Integer(), nullable=False),
        sa.Column('ip', postgresql.INET(), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('host_category', sa.Integer(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=True),
        sa.Column('last_check', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('card_id', sa.Integer(), nullable=True),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('module_item_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['ipv4_networks_id'], ['ipv4_networks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ipv4_networks_id', 'ip')
    )
    op.create_index(op.f('ix_ipv4_ips_id'), 'ipv4_ips', ['id'], unique=False)

    # Create ipv6_networks table
    op.create_table('ipv6_networks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', postgresql.INET(), nullable=False),
        sa.Column('prefix', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('network_category_id', sa.Integer(), nullable=False),
        sa.Column('network_type', sa.String(length=20), nullable=True),
        sa.Column('type_of_usage', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['network_category_id'], ['network_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ipv6_networks_id'), 'ipv6_networks', ['id'], unique=False)

    # Create ipv6_ips table
    op.create_table('ipv6_ips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ipv6_networks_id', sa.Integer(), nullable=False),
        sa.Column('ip', postgresql.INET(), nullable=False),
        sa.Column('ip_end', postgresql.INET(), nullable=True),
        sa.Column('prefix', sa.Integer(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('host_category', sa.Integer(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('card_id', sa.Integer(), nullable=True),
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('module_item_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['ipv6_networks_id'], ['ipv6_networks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ipv6_ips_id'), 'ipv6_ips', ['id'], unique=False)

    # Create routers table
    op.create_table('routers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=255), nullable=True),
        sa.Column('partners_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=False),
        sa.Column('gps', sa.Text(), nullable=True),
        sa.Column('gps_point', sa.String(length=100), nullable=True),
        sa.Column('authorization_method', sa.String(length=50), nullable=True),
        sa.Column('accounting_method', sa.String(length=50), nullable=True),
        sa.Column('nas_type', sa.Integer(), nullable=False),
        sa.Column('nas_ip', postgresql.INET(), nullable=True),
        sa.Column('radius_secret', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('pool_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('api_login', sa.String(length=100), nullable=True),
        sa.Column('api_password', sa.String(length=255), nullable=True),
        sa.Column('api_port', sa.Integer(), nullable=True),
        sa.Column('api_enable', sa.Boolean(), nullable=True),
        sa.Column('api_status', sa.String(length=20), nullable=True),
        sa.Column('shaper', sa.Boolean(), nullable=True),
        sa.Column('shaper_id', sa.Integer(), nullable=True),
        sa.Column('shaping_type', sa.String(length=20), nullable=True),
        sa.Column('last_status', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cpu_usage', sa.Integer(), nullable=True),
        sa.Column('platform', sa.String(length=100), nullable=True),
        sa.Column('board_name', sa.String(length=100), nullable=True),
        sa.Column('version', sa.String(length=100), nullable=True),
        sa.Column('connection_error', sa.Integer(), nullable=True),
        sa.Column('last_api_error', sa.Boolean(), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=True),
        sa.Column('pid', sa.Integer(), nullable=True),
        sa.Column('used_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('change_status', sa.Boolean(), nullable=True),
        sa.Column('change_authorization', sa.Boolean(), nullable=True),
        sa.Column('change_shaping', sa.Boolean(), nullable=True),
        sa.Column('last_connect', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accounting', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip'),
        sa.UniqueConstraint('title')
    )
    op.create_index(op.f('ix_routers_id'), 'routers', ['id'], unique=False)

    # Create router_sectors table
    op.create_table('router_sectors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('router_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('speed_down', sa.Integer(), nullable=False),
        sa.Column('speed_up', sa.Integer(), nullable=False),
        sa.Column('limit_at', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['router_id'], ['routers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_router_sectors_id'), 'router_sectors', ['id'], unique=False)

    # Create monitoring device support tables
    op.create_table('monitoring_device_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_device_types_id'), 'monitoring_device_types', ['id'], unique=False)

    op.create_table('monitoring_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_groups_id'), 'monitoring_groups', ['id'], unique=False)

    op.create_table('monitoring_producers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_producers_id'), 'monitoring_producers', ['id'], unique=False)

    # Create monitoring_devices table
    op.create_table('monitoring_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('network_site_id', sa.Integer(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('producer_id', sa.Integer(), nullable=False),
        sa.Column('model', sa.String(length=255), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=False),
        sa.Column('snmp_port', sa.Integer(), nullable=True),
        sa.Column('is_ping', sa.Boolean(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('snmp_community', sa.String(length=100), nullable=True),
        sa.Column('snmp_version', sa.Integer(), nullable=True),
        sa.Column('type_id', sa.Integer(), nullable=False),
        sa.Column('monitoring_group_id', sa.Integer(), nullable=False),
        sa.Column('partners_ids', postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('send_notifications', sa.Boolean(), nullable=True),
        sa.Column('gps', sa.String(length=100), nullable=True),
        sa.Column('gps_area', sa.Text(), nullable=True),
        sa.Column('delay_timer', sa.Integer(), nullable=True),
        sa.Column('access_device', sa.Boolean(), nullable=True),
        sa.Column('snmp_time', sa.Integer(), nullable=True),
        sa.Column('snmp_uptime', sa.Integer(), nullable=True),
        sa.Column('snmp_status', sa.Integer(), nullable=True),
        sa.Column('snmp_status_1', sa.Integer(), nullable=True),
        sa.Column('snmp_status_2', sa.Integer(), nullable=True),
        sa.Column('snmp_status_3', sa.Integer(), nullable=True),
        sa.Column('snmp_status_4', sa.Integer(), nullable=True),
        sa.Column('snmp_status_5', sa.Integer(), nullable=True),
        sa.Column('snmp_state', sa.String(length=20), nullable=True),
        sa.Column('ping_state', sa.String(length=20), nullable=True),
        sa.Column('versions', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.ForeignKeyConstraint(['monitoring_group_id'], ['monitoring_groups.id'], ),
        sa.ForeignKeyConstraint(['network_site_id'], ['network_sites.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['monitoring_devices.id'], ),
        sa.ForeignKeyConstraint(['producer_id'], ['monitoring_producers.id'], ),
        sa.ForeignKeyConstraint(['type_id'], ['monitoring_device_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip')
    )
    op.create_index(op.f('ix_monitoring_devices_id'), 'monitoring_devices', ['id'], unique=False)

    # Insert default data
    # Default network categories
    op.execute("""
        INSERT INTO network_categories (name) VALUES 
        ('Customer Networks'),
        ('Infrastructure'),
        ('Management'),
        ('Point-to-Point')
        ON CONFLICT DO NOTHING;
    """)

    # Default monitoring device types
    op.execute("""
        INSERT INTO monitoring_device_types (name) VALUES 
        ('Router'),
        ('Switch'),
        ('Access Point'),
        ('Server'),
        ('Firewall')
        ON CONFLICT DO NOTHING;
    """)

    # Default monitoring groups
    op.execute("""
        INSERT INTO monitoring_groups (name) VALUES 
        ('Core Network'),
        ('Access Layer'),
        ('Customer Equipment'),
        ('Servers')
        ON CONFLICT DO NOTHING;
    """)

    # Default monitoring producers
    op.execute("""
        INSERT INTO monitoring_producers (name) VALUES 
        ('MikroTik'),
        ('Cisco'),
        ('Ubiquiti'),
        ('TP-Link'),
        ('Generic')
        ON CONFLICT DO NOTHING;
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('monitoring_devices')
    op.drop_table('monitoring_producers')
    op.drop_table('monitoring_groups')
    op.drop_table('monitoring_device_types')
    op.drop_table('router_sectors')
    op.drop_table('routers')
    op.drop_table('ipv6_ips')
    op.drop_table('ipv6_networks')
    op.drop_table('ipv4_ips')
    op.drop_table('ipv4_networks')
    op.drop_table('network_categories')
    op.drop_table('network_sites')
