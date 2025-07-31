"""Add RADIUS clients table for FreeRADIUS integration

Revision ID: 008_add_radius_clients
Revises: 007_add_radius_tables
Create Date: 2025-01-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_radius_clients'
down_revision = '007_add_radius_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create radius_clients table for FreeRADIUS client configuration
    op.create_table('radius_clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nasname', sa.String(length=128), nullable=False),
        sa.Column('shortname', sa.String(length=32), nullable=True),
        sa.Column('type', sa.String(length=30), nullable=True),
        sa.Column('ports', sa.Integer(), nullable=True),
        sa.Column('secret', sa.String(length=60), nullable=False),
        sa.Column('server', sa.String(length=64), nullable=True),
        sa.Column('community', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nasname')
    )
    op.create_index(op.f('ix_radius_clients_id'), 'radius_clients', ['id'], unique=False)
    op.create_index(op.f('ix_radius_clients_nasname'), 'radius_clients', ['nasname'], unique=True)

    # Insert default RADIUS clients for testing
    op.execute("""
        INSERT INTO radius_clients (nasname, shortname, type, secret, description) VALUES
        ('127.0.0.1', 'localhost', 'other', 'testing123', 'Localhost client for testing'),
        ('172.20.0.0/16', 'docker', 'other', 'testing123', 'Docker network client'),
        ('192.168.1.1', 'mikrotik-main', 'mikrotik', 'mikrotik_secret_123', 'Main MikroTik router'),
        ('192.168.1.2', 'cisco-main', 'cisco', 'cisco_secret_123', 'Main Cisco router'),
        ('10.0.0.0/8', 'isp-network', 'other', 'isp_network_secret_123', 'ISP network range'),
        ('192.168.100.1', 'pppoe-server', 'other', 'pppoe_secret_123', 'PPPoE concentrator');
    """)


def downgrade():
    # Drop radius_clients table
    op.drop_index(op.f('ix_radius_clients_nasname'), table_name='radius_clients')
    op.drop_index(op.f('ix_radius_clients_id'), table_name='radius_clients')
    op.drop_table('radius_clients')
