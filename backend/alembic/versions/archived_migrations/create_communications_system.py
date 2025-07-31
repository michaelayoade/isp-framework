"""Create communications system

Revision ID: create_communications_system
Revises: 
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_communications_system'
down_revision = '2025_07_23_add_api_management'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    communication_type_enum = postgresql.ENUM(
        'email', 'sms', 'push_notification', 'webhook', 'voice_call',
        name='communicationtype'
    )
    communication_type_enum.create(op.get_bind())
    
    communication_status_enum = postgresql.ENUM(
        'pending', 'queued', 'sending', 'sent', 'delivered', 'failed', 'bounced', 'rejected', 'cancelled',
        name='communicationstatus'
    )
    communication_status_enum.create(op.get_bind())
    
    communication_priority_enum = postgresql.ENUM(
        'low', 'normal', 'high', 'urgent', 'critical',
        name='communicationpriority'
    )
    communication_priority_enum.create(op.get_bind())
    
    template_category_enum = postgresql.ENUM(
        'customer_onboarding', 'billing', 'service_alerts', 'support', 'marketing', 'system', 'authentication', 'network',
        name='templatecategory'
    )
    template_category_enum.create(op.get_bind())
    
    # Create communication_templates table
    op.create_table(
        'communication_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', template_category_enum, nullable=False),
        sa.Column('communication_type', communication_type_enum, nullable=False),
        sa.Column('subject_template', sa.Text(), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('html_template', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False),
        sa.Column('language', sa.String(length=10), nullable=True, default='en'),
        sa.Column('required_variables', sa.JSON(), nullable=True, default=sa.text("'[]'::json")),
        sa.Column('optional_variables', sa.JSON(), nullable=True, default=sa.text("'[]'::json")),
        sa.Column('sample_data', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True, default='1.0'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_communication_templates_id'), 'communication_templates', ['id'], unique=False)
    
    # Create communication_providers table
    op.create_table(
        'communication_providers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('provider_type', communication_type_enum, nullable=False),
        sa.Column('provider_class', sa.String(length=255), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('credentials', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('priority', sa.Integer(), nullable=True, default=100),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True, default=60),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True, default=1000),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=True, default=10000),
        sa.Column('success_rate', sa.Integer(), nullable=True, default=100),
        sa.Column('average_delivery_time', sa.Integer(), nullable=True, default=0),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_providers_id'), 'communication_providers', ['id'], unique=False)
    
    # Create communication_logs table
    op.create_table(
        'communication_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('communication_type', communication_type_enum, nullable=False),
        sa.Column('status', communication_status_enum, nullable=True, default='pending'),
        sa.Column('priority', communication_priority_enum, nullable=True, default='normal'),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=50), nullable=True),
        sa.Column('recipient_name', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('context_type', sa.String(length=50), nullable=True),
        sa.Column('context_id', sa.Integer(), nullable=True),
        sa.Column('template_variables', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('provider_response', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=True, default=3),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['provider_id'], ['communication_providers.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['communication_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_logs_id'), 'communication_logs', ['id'], unique=False)
    op.create_index('ix_communication_logs_status', 'communication_logs', ['status'], unique=False)
    op.create_index('ix_communication_logs_customer_id', 'communication_logs', ['customer_id'], unique=False)
    op.create_index('ix_communication_logs_created_at', 'communication_logs', ['created_at'], unique=False)
    
    # Create communication_queue table
    op.create_table(
        'communication_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('queue_name', sa.String(length=255), nullable=False),
        sa.Column('communication_type', communication_type_enum, nullable=False),
        sa.Column('priority', communication_priority_enum, nullable=True, default='normal'),
        sa.Column('total_recipients', sa.Integer(), nullable=True, default=0),
        sa.Column('processed_count', sa.Integer(), nullable=True, default=0),
        sa.Column('success_count', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_count', sa.Integer(), nullable=True, default=0),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('recipients', sa.JSON(), nullable=True, default=sa.text("'[]'::json")),
        sa.Column('template_variables', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provider_id', sa.Integer(), nullable=True),
        sa.Column('batch_size', sa.Integer(), nullable=True, default=100),
        sa.Column('delay_between_batches', sa.Integer(), nullable=True, default=60),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['provider_id'], ['communication_providers.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['communication_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_queue_id'), 'communication_queue', ['id'], unique=False)
    
    # Create communication_preferences table
    op.create_table(
        'communication_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('email_billing', sa.Boolean(), nullable=True, default=True),
        sa.Column('email_service_alerts', sa.Boolean(), nullable=True, default=True),
        sa.Column('email_support', sa.Boolean(), nullable=True, default=True),
        sa.Column('email_marketing', sa.Boolean(), nullable=True, default=False),
        sa.Column('email_system', sa.Boolean(), nullable=True, default=True),
        sa.Column('sms_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('sms_billing', sa.Boolean(), nullable=True, default=False),
        sa.Column('sms_service_alerts', sa.Boolean(), nullable=True, default=True),
        sa.Column('sms_support', sa.Boolean(), nullable=True, default=False),
        sa.Column('sms_marketing', sa.Boolean(), nullable=True, default=False),
        sa.Column('sms_system', sa.Boolean(), nullable=True, default=True),
        sa.Column('push_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('push_billing', sa.Boolean(), nullable=True, default=True),
        sa.Column('push_service_alerts', sa.Boolean(), nullable=True, default=True),
        sa.Column('push_support', sa.Boolean(), nullable=True, default=True),
        sa.Column('push_marketing', sa.Boolean(), nullable=True, default=False),
        sa.Column('push_system', sa.Boolean(), nullable=True, default=True),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True, default='22:00'),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True, default='08:00'),
        sa.Column('timezone', sa.String(length=50), nullable=True, default='UTC'),
        sa.Column('preferred_language', sa.String(length=10), nullable=True, default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )
    op.create_index(op.f('ix_communication_preferences_id'), 'communication_preferences', ['id'], unique=False)
    
    # Create communication_rules table
    op.create_table(
        'communication_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_event', sa.String(length=100), nullable=False),
        sa.Column('trigger_conditions', sa.JSON(), nullable=True, default=sa.text("'{}'::json")),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('communication_type', communication_type_enum, nullable=False),
        sa.Column('priority', communication_priority_enum, nullable=True, default='normal'),
        sa.Column('delay_minutes', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('triggered_count', sa.Integer(), nullable=True, default=0),
        sa.Column('success_count', sa.Integer(), nullable=True, default=0),
        sa.Column('failed_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['communication_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_rules_id'), 'communication_rules', ['id'], unique=False)
    
    # Insert default system templates
    op.execute("""
        INSERT INTO communication_templates (
            name, category, communication_type, subject_template, body_template, 
            is_system, required_variables, description
        ) VALUES 
        (
            'Customer Welcome Email',
            'customer_onboarding',
            'email',
            'Welcome to {{ company_name }}, {{ customer_name }}!',
            'Dear {{ customer_name }},\n\nWelcome to {{ company_name }}! Your account has been created successfully.\n\nAccount Details:\n- Customer ID: {{ customer_id }}\n- Portal ID: {{ portal_id }}\n- Email: {{ email }}\n\nYou can access your customer portal at: {{ portal_url }}\n\nIf you have any questions, please contact our support team.\n\nBest regards,\n{{ company_name }} Team',
            true,
            '["customer_name", "company_name", "customer_id", "portal_id", "email", "portal_url"]',
            'Welcome email sent to new customers'
        ),
        (
            'Service Activation SMS',
            'service_alerts',
            'sms',
            null,
            'Your {{ service_type }} service has been activated. Speed: {{ speed }}. Welcome to {{ company_name }}!',
            true,
            '["service_type", "speed", "company_name"]',
            'SMS notification for service activation'
        ),
        (
            'Invoice Generated Email',
            'billing',
            'email',
            'Invoice #{{ invoice_number }} - {{ company_name }}',
            'Dear {{ customer_name }},\n\nYour invoice #{{ invoice_number }} has been generated.\n\nAmount: {{ currency }}{{ amount }}\nDue Date: {{ due_date }}\n\nYou can view and pay your invoice online at: {{ invoice_url }}\n\nThank you for your business!\n\n{{ company_name }}',
            true,
            '["customer_name", "invoice_number", "amount", "currency", "due_date", "invoice_url", "company_name"]',
            'Email notification for new invoices'
        ),
        (
            'Payment Reminder SMS',
            'billing',
            'sms',
            null,
            'Reminder: Invoice #{{ invoice_number }} ({{ currency }}{{ amount }}) is due {{ due_date }}. Pay online: {{ payment_url }}',
            true,
            '["invoice_number", "amount", "currency", "due_date", "payment_url"]',
            'SMS reminder for overdue payments'
        ),
        (
            'Service Outage Alert',
            'service_alerts',
            'email',
            'Service Outage Notification - {{ company_name }}',
            'Dear {{ customer_name }},\n\nWe are experiencing a service outage in your area.\n\nAffected Services: {{ affected_services }}\nEstimated Resolution: {{ estimated_resolution }}\n\nWe apologize for the inconvenience and are working to restore service as quickly as possible.\n\nFor updates, visit: {{ status_url }}\n\n{{ company_name }} Technical Team',
            true,
            '["customer_name", "affected_services", "estimated_resolution", "status_url", "company_name"]',
            'Email notification for service outages'
        ),
        (
            'Support Ticket Created',
            'support',
            'email',
            'Support Ticket #{{ ticket_number }} Created - {{ company_name }}',
            'Dear {{ customer_name }},\n\nYour support ticket has been created successfully.\n\nTicket #: {{ ticket_number }}\nSubject: {{ ticket_subject }}\nPriority: {{ priority }}\n\nOur support team will respond within {{ sla_response_time }}.\n\nYou can track your ticket at: {{ ticket_url }}\n\nThank you,\n{{ company_name }} Support Team',
            true,
            '["customer_name", "ticket_number", "ticket_subject", "priority", "sla_response_time", "ticket_url", "company_name"]',
            'Email confirmation for new support tickets'
        )
    """)
    
    # Insert default SMTP email provider
    op.execute("""
        INSERT INTO communication_providers (
            name, provider_type, provider_class, configuration, is_default, description
        ) VALUES (
            'Default SMTP Provider',
            'email',
            'SMTPProvider',
            '{"smtp_host": "localhost", "smtp_port": 587, "use_tls": true, "from_email": "noreply@ispframework.com"}',
            true,
            'Default SMTP email provider for ISP Framework'
        )
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('communication_rules')
    op.drop_table('communication_preferences')
    op.drop_table('communication_queue')
    op.drop_table('communication_logs')
    op.drop_table('communication_providers')
    op.drop_table('communication_templates')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS communicationtype')
    op.execute('DROP TYPE IF EXISTS communicationstatus')
    op.execute('DROP TYPE IF EXISTS communicationpriority')
    op.execute('DROP TYPE IF EXISTS templatecategory')
