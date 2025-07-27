"""Fix webhook system migration with existing enum types

Revision ID: fix_webhook_2025_07_24
Revises: create_ticketing_system
Create Date: 2025-07-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_webhook_2025_07_24'
down_revision = 'create_ticketing_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types only if they don't exist
    eventcategory_enum = postgresql.ENUM(
        'CUSTOMER', 'BILLING', 'SERVICE', 'NETWORK', 'TICKETING', 
        'AUTHENTICATION', 'SYSTEM', 'RESELLER', 
        name='eventcategory'
    )
    eventcategory_enum.create(op.get_bind(), checkfirst=True)

    deliverystatus_enum = postgresql.ENUM(
        'PENDING', 'SUCCESS', 'FAILED', 'RETRYING',
        name='deliverystatus'
    )
    deliverystatus_enum.create(op.get_bind(), checkfirst=True)

    # Create webhook event types table
    op.create_table('webhook_event_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', postgresql.ENUM(
            'CUSTOMER', 'BILLING', 'SERVICE', 'NETWORK', 'TICKETING', 
            'AUTHENTICATION', 'SYSTEM', 'RESELLER', name='eventcategory'
        ), nullable=False),
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
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('retry_policy', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhook subscriptions table
    op.create_table('webhook_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('endpoint_id', sa.Integer(), nullable=False),
        sa.Column('event_type_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('filter_criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['endpoint_id'], ['webhook_endpoints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_type_id'], ['webhook_event_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint_id', 'event_type_id', name='unique_endpoint_event_subscription')
    )

    # Create webhook deliveries table
    op.create_table('webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', postgresql.ENUM(
            'PENDING', 'SUCCESS', 'FAILED', 'RETRYING', name='deliverystatus'
        ), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('response_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_after', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['subscription_id'], ['webhook_subscriptions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create webhook retry attempts table
    op.create_table('webhook_retry_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('delivery_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['delivery_id'], ['webhook_deliveries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_webhook_event_types_category', 'webhook_event_types', ['category'])
    op.create_index('idx_webhook_endpoints_is_active', 'webhook_endpoints', ['is_active'])
    op.create_index('idx_webhook_subscriptions_endpoint_id', 'webhook_subscriptions', ['endpoint_id'])
    op.create_index('idx_webhook_subscriptions_event_type_id', 'webhook_subscriptions', ['event_type_id'])
    op.create_index('idx_webhook_deliveries_subscription_id', 'webhook_deliveries', ['subscription_id'])
    op.create_index('idx_webhook_deliveries_status', 'webhook_deliveries', ['status'])
    op.create_index('idx_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'])
    op.create_index('idx_webhook_retry_attempts_delivery_id', 'webhook_retry_attempts', ['delivery_id'])

    # Insert default webhook event types
    op.execute("""
        INSERT INTO webhook_event_types (name, category, description, payload_schema, sample_payload, created_at) VALUES
        ('customer.created', 'CUSTOMER', 'Triggered when a new customer is created', '{"type": "object", "properties": {"customer_id": {"type": "integer"}, "email": {"type": "string"}, "name": {"type": "string"}, "created_at": {"type": "string", "format": "date-time"}}}', '{"customer_id": 123, "email": "john@example.com", "name": "John Doe", "created_at": "2024-01-01T12:00:00Z"}', NOW()),
        ('customer.updated', 'CUSTOMER', 'Triggered when customer information is updated', '{"type": "object", "properties": {"customer_id": {"type": "integer"}, "changes": {"type": "object"}, "updated_at": {"type": "string", "format": "date-time"}}}', '{"customer_id": 123, "changes": {"email": "new@example.com"}, "updated_at": "2024-01-01T13:00:00Z"}', NOW()),
        ('customer.deleted', 'CUSTOMER', 'Triggered when a customer is deleted', '{"type": "object", "properties": {"customer_id": {"type": "integer"}, "deleted_at": {"type": "string", "format": "date-time"}}}', '{"customer_id": 123, "deleted_at": "2024-01-01T14:00:00Z"}', NOW()),
        ('service.activated', 'SERVICE', 'Triggered when a service is activated for a customer', '{"type": "object", "properties": {"customer_id": {"type": "integer"}, "service_id": {"type": "integer"}, "service_type": {"type": "string"}, "activated_at": {"type": "string", "format": "date-time"}}}', '{"customer_id": 123, "service_id": 456, "service_type": "internet", "activated_at": "2024-01-01T15:00:00Z"}', NOW()),
        ('service.suspended', 'SERVICE', 'Triggered when a service is suspended', '{"type": "object", "properties": {"customer_id": {"type": "integer"}, "service_id": {"type": "integer"}, "reason": {"type": "string"}, "suspended_at": {"type": "string", "format": "date-time"}}}', '{"customer_id": 123, "service_id": 456, "reason": "payment_overdue", "suspended_at": "2024-01-01T16:00:00Z"}', NOW()),
        ('billing.invoice_created', 'BILLING', 'Triggered when a new invoice is created', '{"type": "object", "properties": {"invoice_id": {"type": "integer"}, "customer_id": {"type": "integer"}, "amount": {"type": "number"}, "due_date": {"type": "string", "format": "date"}, "created_at": {"type": "string", "format": "date-time"}}}', '{"invoice_id": 789, "customer_id": 123, "amount": 99.99, "due_date": "2024-02-01", "created_at": "2024-01-01T17:00:00Z"}', NOW()),
        ('billing.payment_received', 'BILLING', 'Triggered when a payment is received', '{"type": "object", "properties": {"payment_id": {"type": "integer"}, "customer_id": {"type": "integer"}, "amount": {"type": "number"}, "payment_method": {"type": "string"}, "received_at": {"type": "string", "format": "date-time"}}}', '{"payment_id": 321, "customer_id": 123, "amount": 99.99, "payment_method": "credit_card", "received_at": "2024-01-01T18:00:00Z"}', NOW()),
        ('ticket.created', 'TICKETING', 'Triggered when a new support ticket is created', '{"type": "object", "properties": {"ticket_id": {"type": "integer"}, "customer_id": {"type": "integer"}, "subject": {"type": "string"}, "priority": {"type": "string"}, "created_at": {"type": "string", "format": "date-time"}}}', '{"ticket_id": 555, "customer_id": 123, "subject": "Internet not working", "priority": "high", "created_at": "2024-01-01T19:00:00Z"}', NOW()),
        ('ticket.status_changed', 'TICKETING', 'Triggered when ticket status changes', '{"type": "object", "properties": {"ticket_id": {"type": "integer"}, "old_status": {"type": "string"}, "new_status": {"type": "string"}, "changed_at": {"type": "string", "format": "date-time"}}}', '{"ticket_id": 555, "old_status": "open", "new_status": "in_progress", "changed_at": "2024-01-01T20:00:00Z"}', NOW())
    """)


def downgrade():
    # Drop indexes
    op.drop_index('idx_webhook_retry_attempts_delivery_id', table_name='webhook_retry_attempts')
    op.drop_index('idx_webhook_deliveries_created_at', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_status', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_subscription_id', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_subscriptions_event_type_id', table_name='webhook_subscriptions')
    op.drop_index('idx_webhook_subscriptions_endpoint_id', table_name='webhook_subscriptions')
    op.drop_index('idx_webhook_endpoints_is_active', table_name='webhook_endpoints')
    op.drop_index('idx_webhook_event_types_category', table_name='webhook_event_types')
    
    # Drop tables
    op.drop_table('webhook_retry_attempts')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_subscriptions')
    op.drop_table('webhook_endpoints')
    op.drop_table('webhook_event_types')
    
    # Drop enums (only if they exist and are not used elsewhere)
    op.execute('DROP TYPE IF EXISTS deliverystatus')
    op.execute('DROP TYPE IF EXISTS eventcategory')
