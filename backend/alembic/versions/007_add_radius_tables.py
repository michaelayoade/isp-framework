"""Add RADIUS session management tables

Revision ID: 007_add_radius_tables
Revises: 006_add_network_infrastructure
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_radius_tables'
down_revision = '006_add_network_infrastructure'
branch_labels = None
depends_on = None


def upgrade():
    # Create radius_sessions table
    op.create_table('radius_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('tariff_id', sa.Integer(), nullable=True),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('nas_id', sa.Integer(), nullable=True),
        sa.Column('login', sa.String(length=255), nullable=False),
        sa.Column('username_real', sa.String(length=255), nullable=True),
        sa.Column('in_bytes', sa.BigInteger(), nullable=True),
        sa.Column('out_bytes', sa.BigInteger(), nullable=True),
        sa.Column('start_session', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_session', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ipv4', postgresql.INET(), nullable=True),
        sa.Column('ipv6', postgresql.INET(), nullable=True),
        sa.Column('mac', sa.String(length=17), nullable=True),
        sa.Column('call_to', sa.String(length=50), nullable=True),
        sa.Column('port', sa.String(length=50), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('time_on', sa.Integer(), nullable=True),
        sa.Column('last_change', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('login_is', sa.String(length=20), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('session_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['internet_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_radius_sessions_id'), 'radius_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_radius_sessions_login'), 'radius_sessions', ['login'], unique=False)
    op.create_index(op.f('ix_radius_sessions_start_session'), 'radius_sessions', ['start_session'], unique=False)
    op.create_index(op.f('ix_radius_sessions_session_id'), 'radius_sessions', ['session_id'], unique=False)
    op.create_index(op.f('ix_radius_sessions_session_status'), 'radius_sessions', ['session_status'], unique=False)

    # Create customers_online table
    op.create_table('customers_online',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('tariff_id', sa.Integer(), nullable=True),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('nas_id', sa.Integer(), nullable=True),
        sa.Column('login', sa.String(length=255), nullable=False),
        sa.Column('username_real', sa.String(length=255), nullable=True),
        sa.Column('in_bytes', sa.BigInteger(), nullable=True),
        sa.Column('out_bytes', sa.BigInteger(), nullable=True),
        sa.Column('start_session', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ipv4', postgresql.INET(), nullable=True),
        sa.Column('ipv6', postgresql.INET(), nullable=True),
        sa.Column('mac', sa.String(length=17), nullable=True),
        sa.Column('call_to', sa.String(length=50), nullable=True),
        sa.Column('port', sa.String(length=50), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('time_on', sa.Integer(), nullable=True),
        sa.Column('last_change', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('login_is', sa.String(length=20), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['internet_services.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_customers_online_id'), 'customers_online', ['id'], unique=False)
    op.create_index(op.f('ix_customers_online_login'), 'customers_online', ['login'], unique=False)
    op.create_index(op.f('ix_customers_online_start_session'), 'customers_online', ['start_session'], unique=False)
    op.create_index(op.f('ix_customers_online_ipv4'), 'customers_online', ['ipv4'], unique=False)
    op.create_index(op.f('ix_customers_online_mac'), 'customers_online', ['mac'], unique=False)
    op.create_index(op.f('ix_customers_online_session_id'), 'customers_online', ['session_id'], unique=True)

    # Create customer_statistics table
    op.create_table('customer_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('tariff_id', sa.Integer(), nullable=True),
        sa.Column('partner_id', sa.Integer(), nullable=True),
        sa.Column('nas_id', sa.Integer(), nullable=True),
        sa.Column('login', sa.String(length=255), nullable=True),
        sa.Column('in_bytes', sa.BigInteger(), nullable=True),
        sa.Column('out_bytes', sa.BigInteger(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ipv4', postgresql.INET(), nullable=True),
        sa.Column('ipv6', postgresql.INET(), nullable=True),
        sa.Column('mac', sa.String(length=17), nullable=True),
        sa.Column('call_to', sa.String(length=50), nullable=True),
        sa.Column('port', sa.String(length=50), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('time_on', sa.Integer(), nullable=True),
        sa.Column('last_change', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('login_is', sa.String(length=20), nullable=True),
        sa.Column('period_type', sa.String(length=20), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customer_statistics_id'), 'customer_statistics', ['id'], unique=False)
    op.create_index(op.f('ix_customer_statistics_login'), 'customer_statistics', ['login'], unique=False)
    op.create_index(op.f('ix_customer_statistics_start_date'), 'customer_statistics', ['start_date'], unique=False)
    op.create_index(op.f('ix_customer_statistics_end_date'), 'customer_statistics', ['end_date'], unique=False)
    op.create_index(op.f('ix_customer_statistics_period_type'), 'customer_statistics', ['period_type'], unique=False)
    op.create_index(op.f('ix_customer_statistics_period_start'), 'customer_statistics', ['period_start'], unique=False)
    op.create_index(op.f('ix_customer_statistics_period_end'), 'customer_statistics', ['period_end'], unique=False)

    # Set default values for existing columns
    op.execute("UPDATE radius_sessions SET in_bytes = 0 WHERE in_bytes IS NULL")
    op.execute("UPDATE radius_sessions SET out_bytes = 0 WHERE out_bytes IS NULL")
    op.execute("UPDATE radius_sessions SET price = 0 WHERE price IS NULL")
    op.execute("UPDATE radius_sessions SET time_on = 0 WHERE time_on IS NULL")
    op.execute("UPDATE radius_sessions SET type = 'mikrotik_api' WHERE type IS NULL")
    op.execute("UPDATE radius_sessions SET login_is = 'user' WHERE login_is IS NULL")
    op.execute("UPDATE radius_sessions SET session_status = 'active' WHERE session_status IS NULL")

    op.execute("UPDATE customers_online SET in_bytes = 0 WHERE in_bytes IS NULL")
    op.execute("UPDATE customers_online SET out_bytes = 0 WHERE out_bytes IS NULL")
    op.execute("UPDATE customers_online SET price = 0 WHERE price IS NULL")
    op.execute("UPDATE customers_online SET time_on = 0 WHERE time_on IS NULL")
    op.execute("UPDATE customers_online SET type = 'mikrotik_api' WHERE type IS NULL")
    op.execute("UPDATE customers_online SET login_is = 'user' WHERE login_is IS NULL")

    op.execute("UPDATE customer_statistics SET in_bytes = 0 WHERE in_bytes IS NULL")
    op.execute("UPDATE customer_statistics SET out_bytes = 0 WHERE out_bytes IS NULL")
    op.execute("UPDATE customer_statistics SET price = 0 WHERE price IS NULL")
    op.execute("UPDATE customer_statistics SET time_on = 0 WHERE time_on IS NULL")
    op.execute("UPDATE customer_statistics SET type = 'mikrotik_api' WHERE type IS NULL")
    op.execute("UPDATE customer_statistics SET login_is = 'user' WHERE login_is IS NULL")
    op.execute("UPDATE customer_statistics SET period_type = 'daily' WHERE period_type IS NULL")


def downgrade():
    # Drop customer_statistics table
    op.drop_index(op.f('ix_customer_statistics_period_end'), table_name='customer_statistics')
    op.drop_index(op.f('ix_customer_statistics_period_start'), table_name='customer_statistics')
    op.drop_index(op.f('ix_customer_statistics_period_type'), table_name='customer_statistics')
    op.drop_index(op.f('ix_customer_statistics_end_date'), table_name='customer_statistics')
    op.drop_index(op.f('ix_customer_statistics_start_date'), table_name='customer_statistics')
    op.drop_index(op.f('ix_customer_statistics_login'), table_name='customer_statistics')
    op.drop_index(op.f('ix_customer_statistics_id'), table_name='customer_statistics')
    op.drop_table('customer_statistics')

    # Drop customers_online table
    op.drop_index(op.f('ix_customers_online_session_id'), table_name='customers_online')
    op.drop_index(op.f('ix_customers_online_mac'), table_name='customers_online')
    op.drop_index(op.f('ix_customers_online_ipv4'), table_name='customers_online')
    op.drop_index(op.f('ix_customers_online_start_session'), table_name='customers_online')
    op.drop_index(op.f('ix_customers_online_login'), table_name='customers_online')
    op.drop_index(op.f('ix_customers_online_id'), table_name='customers_online')
    op.drop_table('customers_online')

    # Drop radius_sessions table
    op.drop_index(op.f('ix_radius_sessions_session_status'), table_name='radius_sessions')
    op.drop_index(op.f('ix_radius_sessions_session_id'), table_name='radius_sessions')
    op.drop_index(op.f('ix_radius_sessions_start_session'), table_name='radius_sessions')
    op.drop_index(op.f('ix_radius_sessions_login'), table_name='radius_sessions')
    op.drop_index(op.f('ix_radius_sessions_id'), table_name='radius_sessions')
    op.drop_table('radius_sessions')
