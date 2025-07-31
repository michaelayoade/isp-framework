"""
Add API Management Tables

Revision ID: 2025_07_23_add_api_management
Revises: 2025_07_23_enhanced_billing
Create Date: 2025-07-23 15:00:00.000000

This migration adds comprehensive API management functionality to the ISP Framework:
- API key management with security features
- Usage tracking and analytics
- Rate limiting and quota enforcement
- API versioning and documentation
- Access control and permissions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_07_23_add_api_management'
down_revision = 'create_api_management_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('key_name', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False, unique=True),
        sa.Column('api_secret', sa.String(255), nullable=False),
        sa.Column('partner_id', sa.Integer(), sa.ForeignKey('partners.id'), nullable=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('administrators.id'), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('scopes', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('rate_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('daily_quota', sa.Integer(), nullable=False, server_default='10000'),
        sa.Column('monthly_quota', sa.Integer(), nullable=False, server_default='100000'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_whitelist', postgresql.JSONB(), nullable=True),
        sa.Column('referrer_whitelist', postgresql.JSONB(), nullable=True),
        sa.Column('user_agent_whitelist', postgresql.JSONB(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Index('ix_api_keys_api_key', 'api_key', unique=True),
        sa.Index('ix_api_keys_partner_id', 'partner_id'),
    )

    # Create api_management_usage_logs table
    op.create_table(
        'api_management_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('api_key_id', sa.Integer(), sa.ForeignKey('api_management_keys.id'), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=False),
        sa.Column('request_size_bytes', sa.Integer(), nullable=False),
        sa.Column('response_size_bytes', sa.Integer(), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Index('ix_api_management_usage_logs_api_key_id', 'api_key_id'),
        sa.Index('ix_api_management_usage_logs_endpoint', 'endpoint'),
        sa.Index('ix_api_management_usage_logs_method', 'method'),
        sa.Index('ix_api_management_usage_logs_status_code', 'status_code'),
        sa.Index('ix_api_management_usage_logs_created_at', 'created_at'),
        sa.Index('ix_api_management_usage_logs_client_ip', 'client_ip')
    )

    # Create api_management_rate_limit_tracking table
    op.create_table(
        'api_management_rate_limit_tracking',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('api_key_id', sa.Integer(), sa.ForeignKey('api_management_keys.id'), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=True),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('limit_period', sa.Enum('minute', 'hour', 'day', name='ratelimitperiod'), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('limit_value', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Index('ix_api_management_rate_limit_tracking_api_key_id', 'api_key_id'),
        sa.Index('ix_api_management_rate_limit_tracking_endpoint', 'endpoint'),
        sa.Index('ix_api_management_rate_limit_tracking_window_start', 'window_start'),
        sa.Index('ix_api_management_rate_limit_tracking_window_end', 'window_end'),
        sa.UniqueConstraint('api_key_id', 'endpoint', 'window_start')
    )

    # Create api_management_versions table
    op.create_table(
        'api_management_versions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('version', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sunset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('documentation_url', sa.String(500), nullable=True),
        sa.Column('changelog_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Index('ix_api_management_versions_version', 'version', unique=True),
        sa.Index('ix_api_management_versions_status', 'status'),
        sa.Index('ix_api_management_versions_is_default', 'is_default')
    )

    # Create api_management_endpoints table
    op.create_table(
        'api_management_endpoints',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('api_version_id', sa.Integer(), sa.ForeignKey('api_management_versions.id'), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('summary', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('parameters', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('request_body', postgresql.JSONB(), nullable=True),
        sa.Column('responses', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('authentication_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('scopes_required', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('deprecated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Index('ix_api_management_endpoints_api_version_id', 'api_version_id'),
        sa.Index('ix_api_management_endpoints_path', 'path'),
        sa.Index('ix_api_management_endpoints_method', 'method'),
        sa.Index('ix_api_management_endpoints_category', 'category'),
        sa.UniqueConstraint('api_version_id', 'path', 'method')
    )

    # Create api_management_quotas table
    op.create_table(
        'api_management_quotas',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('api_key_id', sa.Integer(), sa.ForeignKey('api_management_keys.id'), nullable=False),
        sa.Column('quota_type', sa.String(20), nullable=False),  # daily, monthly, custom
        sa.Column('limit_value', sa.Integer(), nullable=False),
        sa.Column('current_usage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.Index('ix_api_management_quotas_api_key_id', 'api_key_id'),
        sa.Index('ix_api_management_quotas_quota_type', 'quota_type'),
        sa.Index('ix_api_management_quotas_period_start', 'period_start'),
        sa.Index('ix_api_management_quotas_period_end', 'period_end')
    )

    # Insert default API version
    op.execute("""
        INSERT INTO api_management_versions (version, title, description, base_url, status, is_default)
        VALUES ('v1', 'ISP Framework API v1', 'Initial version of ISP Framework API', '/api/v1', 'active', true)
    """)

    # Add triggers for updated_at columns
    tables_with_updated_at = ['api_management_keys', 'api_management_usage_logs', 'api_management_rate_limit_tracking', 'api_management_versions', 'api_management_endpoints', 'api_management_quotas']
    
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE OR REPLACE FUNCTION update_{table}_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER update_{table}_updated_at_trigger
                BEFORE UPDATE ON {table}
                FOR EACH ROW
                EXECUTE FUNCTION update_{table}_updated_at();
        """)


def downgrade():
    # Drop triggers
    tables_with_updated_at = ['api_management_keys', 'api_management_usage_logs', 'api_management_rate_limit_tracking', 'api_management_versions', 'api_management_endpoints', 'api_management_quotas']
    
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at_trigger ON {table}")
        op.execute(f"DROP FUNCTION IF EXISTS update_{table}_updated_at()")

    # Drop tables in reverse order
    op.drop_table('api_management_quotas')
    op.drop_table('api_management_endpoints')
    op.drop_table('api_management_versions')
    op.drop_table('api_management_rate_limit_tracking')
    op.drop_table('api_management_usage_logs')
    op.drop_table('api_management_keys')
