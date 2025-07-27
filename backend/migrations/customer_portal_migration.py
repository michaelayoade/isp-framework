"""
Customer Portal Database Migration
Creates all customer portal tables for self-service functionality
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime


def upgrade():
    """Create customer portal tables"""
    
    # Customer Portal Sessions
    op.create_table(
        'customer_portal_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False),
        sa.Column('session_type', sa.String(50), nullable=False, default='web'),
        sa.Column('device_info', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('login_method', sa.String(50), nullable=False, default='password'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('logged_out_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.Index('idx_customer_portal_sessions_token', 'session_token'),
        sa.Index('idx_customer_portal_sessions_customer', 'customer_id'),
        sa.Index('idx_customer_portal_sessions_active', 'is_active', 'expires_at')
    )
    
    # Customer Portal Preferences
    op.create_table(
        'customer_portal_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(10), nullable=False, default='en'),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, default=True),
        sa.Column('sms_notifications', sa.Boolean(), nullable=False, default=False),
        sa.Column('marketing_emails', sa.Boolean(), nullable=False, default=True),
        sa.Column('invoice_delivery', sa.String(20), nullable=False, default='email'),
        sa.Column('auto_pay_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('dashboard_layout', sa.String(20), nullable=False, default='standard'),
        sa.Column('theme', sa.String(20), nullable=False, default='light'),
        sa.Column('custom_preferences', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('customer_id')
    )
    
    # Customer Portal Payments
    op.create_table(
        'customer_portal_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('payment_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('payment_method', sa.String(50), nullable=False),
        sa.Column('payment_reference', sa.String(100), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('payment_gateway', sa.String(50), nullable=True),
        sa.Column('external_payment_id', sa.String(255), nullable=True),
        sa.Column('invoice_ids', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('payment_method_token', sa.String(255), nullable=True),
        sa.Column('last_four_digits', sa.String(4), nullable=True),
        sa.Column('card_brand', sa.String(20), nullable=True),
        sa.Column('billing_name', sa.String(255), nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=True),
        sa.Column('billing_address', postgresql.JSONB(), nullable=True),
        sa.Column('processor_fee', sa.Numeric(10, 2), nullable=True),
        sa.Column('net_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('gateway_response', postgresql.JSONB(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('payment_reference'),
        sa.Index('idx_customer_portal_payments_customer', 'customer_id'),
        sa.Index('idx_customer_portal_payments_status', 'status'),
        sa.Index('idx_customer_portal_payments_date', 'created_at')
    )
    
    # Customer Portal Auto Payments
    op.create_table(
        'customer_portal_auto_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('payment_method_token', sa.String(255), nullable=False),
        sa.Column('payment_method_type', sa.String(50), nullable=False),
        sa.Column('last_four_digits', sa.String(4), nullable=True),
        sa.Column('card_brand', sa.String(20), nullable=True),
        sa.Column('auto_pay_amount_type', sa.String(20), nullable=False, default='full_balance'),
        sa.Column('fixed_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('auto_pay_day', sa.Integer(), nullable=False, default=5),
        sa.Column('advance_notice_days', sa.Integer(), nullable=False, default=5),
        sa.Column('max_payment_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('require_confirmation', sa.Boolean(), nullable=False, default=False),
        sa.Column('next_payment_date', sa.Date(), nullable=True),
        sa.Column('last_payment_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_failures', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('customer_id')
    )
    
    # Customer Portal Service Requests
    op.create_table(
        'customer_portal_service_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('request_type', sa.String(50), nullable=False),
        sa.Column('request_title', sa.String(255), nullable=False),
        sa.Column('request_description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('current_service_id', sa.Integer(), nullable=True),
        sa.Column('requested_tariff_id', sa.Integer(), nullable=True),
        sa.Column('requested_add_ons', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_date', sa.Date(), nullable=True),
        sa.Column('urgency', sa.String(20), nullable=False, default='normal'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('estimated_monthly_change', sa.Numeric(10, 2), nullable=True),
        sa.Column('one_time_fees', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('requires_technician', sa.Boolean(), nullable=False, default=False),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_ticket_id', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.Index('idx_customer_portal_service_requests_customer', 'customer_id'),
        sa.Index('idx_customer_portal_service_requests_status', 'status'),
        sa.Index('idx_customer_portal_service_requests_type', 'request_type')
    )
    
    # Customer Portal Notifications
    op.create_table(
        'customer_portal_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, default='normal'),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, default=False),
        sa.Column('action_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('action_text', sa.String(100), nullable=True),
        sa.Column('related_service_id', sa.Integer(), nullable=True),
        sa.Column('related_invoice_id', sa.Integer(), nullable=True),
        sa.Column('related_payment_id', sa.Integer(), nullable=True),
        sa.Column('auto_dismiss_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.Index('idx_customer_portal_notifications_customer', 'customer_id'),
        sa.Index('idx_customer_portal_notifications_unread', 'customer_id', 'is_read'),
        sa.Index('idx_customer_portal_notifications_type', 'notification_type')
    )
    
    # Customer Portal FAQ
    op.create_table(
        'customer_portal_faq',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('helpful_count', sa.Integer(), nullable=False, default=0),
        sa.Column('not_helpful_count', sa.Integer(), nullable=False, default=0),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_customer_portal_faq_category', 'category'),
        sa.Index('idx_customer_portal_faq_active', 'is_active', 'display_order')
    )
    
    # Customer Portal Activity Log
    op.create_table(
        'customer_portal_activity',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('action_description', sa.String(500), nullable=False),
        sa.Column('page_url', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('additional_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['customer_portal_sessions.id'], ondelete='SET NULL'),
        sa.Index('idx_customer_portal_activity_customer', 'customer_id'),
        sa.Index('idx_customer_portal_activity_type', 'activity_type'),
        sa.Index('idx_customer_portal_activity_date', 'created_at')
    )
    
    # Customer Portal Invoice Views (for portal-specific invoice display)
    op.create_table(
        'customer_portal_invoice_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_downloaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_reminder_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('customer_id', 'invoice_id'),
        sa.Index('idx_customer_portal_invoice_views_customer', 'customer_id')
    )
    
    # Customer Portal Usage Views (for portal-specific usage display)
    op.create_table(
        'customer_portal_usage_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('data_used_gb', sa.Numeric(12, 3), nullable=False, default=0),
        sa.Column('data_limit_gb', sa.Numeric(12, 3), nullable=True),
        sa.Column('usage_percentage', sa.Numeric(5, 2), nullable=False, default=0),
        sa.Column('overage_gb', sa.Numeric(12, 3), nullable=False, default=0),
        sa.Column('overage_charges', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('peak_usage_date', sa.Date(), nullable=True),
        sa.Column('daily_usage', postgresql.JSONB(), nullable=True),
        sa.Column('quality_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('customer_id', 'service_id', 'period_start', 'period_end'),
        sa.Index('idx_customer_portal_usage_views_customer', 'customer_id'),
        sa.Index('idx_customer_portal_usage_views_service', 'service_id'),
        sa.Index('idx_customer_portal_usage_views_period', 'period_start', 'period_end')
    )


def downgrade():
    """Drop customer portal tables"""
    op.drop_table('customer_portal_usage_views')
    op.drop_table('customer_portal_invoice_views')
    op.drop_table('customer_portal_activity')
    op.drop_table('customer_portal_faq')
    op.drop_table('customer_portal_notifications')
    op.drop_table('customer_portal_service_requests')
    op.drop_table('customer_portal_auto_payments')
    op.drop_table('customer_portal_payments')
    op.drop_table('customer_portal_preferences')
    op.drop_table('customer_portal_sessions')
