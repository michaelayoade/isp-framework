"""
Create API Management System

Revision ID: create_api_management_system
Revises: create_ticketing_system
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_api_management_system'
down_revision = 'webhook_system_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create API key status enum
    api_key_status = postgresql.ENUM('active', 'inactive', 'revoked', 'expired', name='apikeystatus')
    api_key_status.create(op.get_bind())
    
    # Create rate limit period enum
    rate_limit_period = postgresql.ENUM('second', 'minute', 'hour', 'day', name='ratelimitperiod')
    rate_limit_period.create(op.get_bind())
    
    # Create API keys table
    op.create_table(
        'api_management_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=False),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'revoked', 'expired', name='apikeystatus'), nullable=False),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.text('now()')),
        sa.Column('created_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('reseller_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['administrators.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['reseller_id'], ['resellers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        sa.Index('ix_api_management_keys_key_hash', 'key_hash'),
        sa.Index('ix_api_management_keys_status', 'status'),
        sa.Index('ix_api_management_keys_customer_id', 'customer_id'),
        sa.Index('ix_api_management_keys_reseller_id', 'reseller_id')
    )
    
    # Create API usage logs table
    op.create_table(
        'api_management_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('request_size', sa.Integer(), nullable=True),
        sa.Column('response_size', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_management_keys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create rate limit tracking table
    op.create_table(
        'api_management_rate_limit_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_management_keys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key_id', 'endpoint', 'window_start')
    )
    
    # Create API versioning table
    op.create_table(
        'api_management_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_url', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sunset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('migration_guide_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
        sa.Index('ix_api_management_versions_status', 'status'),
        sa.Index('ix_api_management_versions_created_at', 'created_at')
    )
    
    # Create API quotas table
    op.create_table(
        'api_management_quotas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('quota_type', sa.String(50), nullable=False),  # daily, monthly, custom
        sa.Column('max_requests', sa.Integer(), nullable=False),
        sa.Column('current_usage', sa.Integer(), nullable=False, default=0),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reset_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_api_keys_key', 'api_keys', ['key'], unique=True)
    op.create_index('ix_api_keys_status', 'api_keys', ['status'])
    op.create_index('ix_api_keys_customer_id', 'api_keys', ['customer_id'])
    op.create_index('ix_api_keys_reseller_id', 'api_keys', ['reseller_id'])
    op.create_index('ix_api_keys_admin_id', 'api_keys', ['admin_id'])
    op.create_index('ix_api_keys_expires_at', 'api_keys', ['expires_at'])
    
    op.create_index('ix_api_usage_logs_api_key_id', 'api_usage_logs', ['api_key_id'])
    op.create_index('ix_api_usage_logs_endpoint', 'api_usage_logs', ['endpoint'])
    op.create_index('ix_api_usage_logs_created_at', 'api_usage_logs', ['created_at'])
    op.create_index('ix_api_usage_logs_status_code', 'api_usage_logs', ['status_code'])
    
    op.create_index('ix_rate_limit_tracking_api_key_id', 'rate_limit_tracking', ['api_key_id'])
    op.create_index('ix_rate_limit_tracking_endpoint', 'rate_limit_tracking', ['endpoint'])
    op.create_index('ix_rate_limit_tracking_window_start', 'rate_limit_tracking', ['window_start'])
    
    op.create_index('ix_api_quotas_api_key_id', 'api_quotas', ['api_key_id'])
    op.create_index('ix_api_quotas_period_start', 'api_quotas', ['period_start'])
    op.create_index('ix_api_quotas_period_end', 'api_quotas', ['period_end'])
    
    # Insert default API version
    op.execute("""
        INSERT INTO api_versions (version, description, is_deprecated, changelog)
        VALUES ('v1', 'Initial API version with full ISP management capabilities', false, '{"changes": ["Initial release"]}')
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_api_quotas_period_end', table_name='api_quotas')
    op.drop_index('ix_api_quotas_period_start', table_name='api_quotas')
    op.drop_index('ix_api_quotas_api_key_id', table_name='api_quotas')
    
    op.drop_index('ix_rate_limit_tracking_window_start', table_name='rate_limit_tracking')
    op.drop_index('ix_rate_limit_tracking_endpoint', table_name='rate_limit_tracking')
    op.drop_index('ix_rate_limit_tracking_api_key_id', table_name='rate_limit_tracking')
    
    op.drop_index('ix_api_usage_logs_status_code', table_name='api_usage_logs')
    op.drop_index('ix_api_usage_logs_created_at', table_name='api_usage_logs')
    op.drop_index('ix_api_usage_logs_endpoint', table_name='api_usage_logs')
    op.drop_index('ix_api_usage_logs_api_key_id', table_name='api_usage_logs')
    
    op.drop_index('ix_api_keys_expires_at', table_name='api_keys')
    op.drop_index('ix_api_keys_admin_id', table_name='api_keys')
    op.drop_index('ix_api_keys_reseller_id', table_name='api_keys')
    op.drop_index('ix_api_keys_customer_id', table_name='api_keys')
    sa.Column('status', sa.Enum('active', 'inactive', 'revoked', 'expired', name='apikeystatus'), nullable=False, default='active'),
    op.drop_index('ix_api_keys_status', table_name='api_keys')
    op.drop_index('ix_api_keys_key', table_name='api_keys')
    
    # Drop tables
    op.drop_table('api_management_quotas')
    op.drop_table('api_management_versions')
    op.drop_table('api_management_rate_limit_tracking')
    op.drop_table('api_management_usage_logs')
    op.drop_table('api_management_keys')
    
    # Drop enums
    rate_limit_period = postgresql.ENUM('second', 'minute', 'hour', 'day', name='ratelimitperiod')
    rate_limit_period.drop(op.get_bind())
    
    api_key_status = postgresql.ENUM('active', 'inactive', 'revoked', 'expired', name='apikeystatus')
    api_key_status.drop(op.get_bind())
