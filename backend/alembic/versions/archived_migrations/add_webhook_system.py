"""Add webhook system tables

Revision ID: webhook_system_001
Revises: 
Create Date: 2025-01-25 15:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'webhook_system_001'
down_revision = 'create_ticketing_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create eventcategory enum if it doesn't exist
    eventcategory_enum = postgresql.ENUM('CUSTOMER', 'BILLING', 'SERVICE', 'NETWORK', 'TICKETING', 'AUTHENTICATION', 'SYSTEM', 'RESELLER', name='eventcategory')
    eventcategory_enum.create(op.get_bind(), checkfirst=True)

    # Create webhook event types table
    op.create_table('webhook_event_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', postgresql.ENUM('CUSTOMER', 'BILLING', 'SERVICE', 'NETWORK', 'TICKETING', 'AUTHENTICATION', 'SYSTEM', 'RESELLER', name='eventcategory'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('payload_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sample_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('requires_authentication', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_retry_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create webhook endpoints table
    op.create_table('webhook_endpoints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('http_method', sa.Enum('GET', 'POST', 'PUT', 'PATCH', 'DELETE', name='httpmethod'), nullable=False, default='POST'),
        sa.Column('content_type', sa.Enum('JSON', 'XML', 'FORM_URLENCODED', 'PLAIN_TEXT', name='contenttype'), nullable=False, default='JSON'),
        sa.Column('custom_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('verify_ssl', sa.Boolean(), nullable=False, default=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=30),
        sa.Column('retry_strategy', sa.Enum('EXPONENTIAL_BACKOFF', 'LINEAR_BACKOFF', 'FIXED_INTERVAL', 'IMMEDIATE', name='retrystrategy'), nullable=False, default='EXPONENTIAL_BACKOFF'),
        sa.Column('max_retry_attempts', sa.Integer(), nullable=False, default=5),
        sa.Column('retry_delay_seconds', sa.Integer(), nullable=False, default=60),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False, default=60),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=False, default=1000),
        sa.Column('enable_filtering', sa.Boolean(), nullable=False, default=False),
        sa.Column('secret_token', sa.String(length=255), nullable=True),
        sa.Column('signature_algorithm', sa.Enum('HMAC_SHA256', 'HMAC_SHA512', 'HMAC_SHA1', name='signaturealgorithm'), nullable=False, default='HMAC_SHA256'),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'ERROR', 'RATE_LIMITED', name='webhookstatus'), nullable=False, default='ACTIVE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('total_deliveries', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_deliveries', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_deliveries', sa.Integer(), nullable=False, default=0),
        sa.Column('last_delivery_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failure_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhook events table
    op.create_table('webhook_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('event_type_id', sa.Integer(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('event_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default={}),
        sa.Column('source_ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('triggered_by_user_id', sa.Integer(), nullable=True),
        sa.Column('triggered_by_customer_id', sa.Integer(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_type_id'], ['webhook_event_types.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )

    # Create webhook deliveries table
    op.create_table('webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('delivery_id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('endpoint_id', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'PROCESSING', 'DELIVERED', 'FAILED', 'CANCELLED', 'RATE_LIMITED', name='deliverystatus'), nullable=False, default='PENDING'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=5),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_url', sa.String(length=2048), nullable=True),
        sa.Column('request_method', sa.String(length=10), nullable=True),
        sa.Column('request_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('response_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['endpoint_id'], ['webhook_endpoints.id'], ),
        sa.ForeignKeyConstraint(['event_id'], ['webhook_events.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('delivery_id')
    )

    # Create webhook filters table
    op.create_table('webhook_filters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('endpoint_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('field_path', sa.String(length=500), nullable=False),
        sa.Column('operator', postgresql.ENUM('EQUALS', 'NOT_EQUALS', 'CONTAINS', 'NOT_CONTAINS', 'STARTS_WITH', 'ENDS_WITH', 'IN', 'NOT_IN', 'EXISTS', 'NOT_EXISTS', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUAL', 'LESS_THAN_OR_EQUAL', name='filteroperator'), nullable=False),
        sa.Column('value', sa.String(length=1000), nullable=True),
        sa.Column('values', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('include_on_match', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['endpoint_id'], ['webhook_endpoints.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhook delivery attempts table
    op.create_table('webhook_delivery_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('delivery_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('dns_resolution_time_ms', sa.Integer(), nullable=True),
        sa.Column('connection_time_ms', sa.Integer(), nullable=True),
        sa.Column('ssl_handshake_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_successful', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['delivery_id'], ['webhook_deliveries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhook endpoint subscriptions table
    op.create_table('webhook_endpoint_subscriptions',
        sa.Column('endpoint_id', sa.Integer(), nullable=False),
        sa.Column('event_type_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['endpoint_id'], ['webhook_endpoints.id'], ),
        sa.ForeignKeyConstraint(['event_type_id'], ['webhook_event_types.id'], ),
        sa.PrimaryKeyConstraint('endpoint_id', 'event_type_id')
    )

    # Create indexes for performance
    op.create_index('idx_webhook_events_event_type_id', 'webhook_events', ['event_type_id'])
    op.create_index('idx_webhook_events_occurred_at', 'webhook_events', ['occurred_at'])
    op.create_index('idx_webhook_events_is_processed', 'webhook_events', ['is_processed'])
    op.create_index('idx_webhook_deliveries_endpoint_id', 'webhook_deliveries', ['endpoint_id'])
    op.create_index('idx_webhook_deliveries_status', 'webhook_deliveries', ['status'])
    op.create_index('idx_webhook_deliveries_scheduled_at', 'webhook_deliveries', ['scheduled_at'])
    op.create_index('idx_webhook_filters_endpoint_id', 'webhook_filters', ['endpoint_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_webhook_filters_endpoint_id', table_name='webhook_filters')
    op.drop_index('idx_webhook_deliveries_scheduled_at', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_status', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_endpoint_id', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_events_is_processed', table_name='webhook_events')
    op.drop_index('idx_webhook_events_occurred_at', table_name='webhook_events')
    op.drop_index('idx_webhook_events_event_type_id', table_name='webhook_events')
    
    # Drop tables
    op.drop_table('webhook_filters')
    op.drop_table('webhook_retry_attempts')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_subscriptions')
    op.drop_table('webhook_endpoints')
    op.drop_table('webhook_event_types')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS eventcategory')
    op.execute('DROP TYPE IF EXISTS deliverystatus')
    op.execute('DROP TYPE IF EXISTS signaturealgorithm')
    op.execute('DROP TYPE IF EXISTS webhookstatus')
    op.execute('DROP TYPE IF EXISTS deliverystatus')
    op.execute('DROP TYPE IF EXISTS filteroperator')
