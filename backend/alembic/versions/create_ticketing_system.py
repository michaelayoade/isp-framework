"""create ticketing system

Revision ID: create_ticketing_system
Revises: 
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_ticketing_system'
down_revision = '9e1c7b520e78'
depends_on = None


def upgrade():
    # Create enum types
    tickettype_enum = postgresql.ENUM('support', 'technical', 'incident', 'maintenance', 'field_work', 'abuse', 'complaint', 'compliment', name='tickettype')
    tickettype_enum.create(op.get_bind())
    
    ticketpriority_enum = postgresql.ENUM('low', 'normal', 'high', 'urgent', 'critical', name='ticketpriority')
    ticketpriority_enum.create(op.get_bind())
    
    ticketstatus_enum = postgresql.ENUM('new', 'assigned', 'in_progress', 'pending_customer', 'pending_vendor', 'escalated', 'resolved', 'closed', 'cancelled', name='ticketstatus')
    ticketstatus_enum.create(op.get_bind())
    
    ticketsource_enum = postgresql.ENUM('customer_portal', 'phone', 'email', 'chat', 'walk_in', 'system_automated', 'monitoring', 'staff', 'api', name='ticketsource')
    ticketsource_enum.create(op.get_bind())
    
    escalationreason_enum = postgresql.ENUM('sla_breach', 'customer_request', 'complexity', 'manager_decision', 'repeated_issue', name='escalationreason')
    escalationreason_enum.create(op.get_bind())
    
    fieldworkstatus_enum = postgresql.ENUM('scheduled', 'dispatched', 'en_route', 'on_site', 'completed', 'cancelled', 'rescheduled', name='fieldworkstatus')
    fieldworkstatus_enum.create(op.get_bind())

    # Create SLA policies table
    op.create_table('sla_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ticket_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('customer_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('first_response_time', sa.Integer(), nullable=False),
        sa.Column('critical_resolution_time', sa.Integer(), nullable=False),
        sa.Column('urgent_resolution_time', sa.Integer(), nullable=False),
        sa.Column('high_resolution_time', sa.Integer(), nullable=False),
        sa.Column('normal_resolution_time', sa.Integer(), nullable=False),
        sa.Column('low_resolution_time', sa.Integer(), nullable=False),
        sa.Column('auto_escalate_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('escalation_threshold_percent', sa.Integer(), nullable=False, default=80),
        sa.Column('business_hours_only', sa.Boolean(), nullable=False, default=False),
        sa.Column('business_hours_start', sa.String(length=5), nullable=False, default='09:00'),
        sa.Column('business_hours_end', sa.String(length=5), nullable=False, default='17:00'),
        sa.Column('business_days', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, default='UTC'),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sla_policies_name', 'sla_policies', ['name'])
    op.create_index('ix_sla_policies_is_default', 'sla_policies', ['is_default'])

    # Create tickets table
    op.create_table('tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(length=50), nullable=False),
        sa.Column('ticket_type', tickettype_enum, nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', ticketstatus_enum, nullable=False, default='new'),
        sa.Column('priority', ticketpriority_enum, nullable=False, default='normal'),
        sa.Column('urgency', sa.Integer(), nullable=False, default=3),
        sa.Column('impact', sa.Integer(), nullable=False, default=3),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('contact_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('assigned_team', sa.String(length=100), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', ticketsource_enum, nullable=False, default='customer_portal'),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('sla_policy_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_response_due', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_due', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_response_sla_met', sa.Boolean(), nullable=True),
        sa.Column('resolution_sla_met', sa.Boolean(), nullable=True),
        sa.Column('work_location', sa.String(length=255), nullable=True),
        sa.Column('gps_latitude', sa.String(length=20), nullable=True),
        sa.Column('gps_longitude', sa.String(length=20), nullable=True),
        sa.Column('initial_diagnosis', sa.Text(), nullable=True),
        sa.Column('resolution_summary', sa.Text(), nullable=True),
        sa.Column('customer_satisfaction', sa.Integer(), nullable=True),
        sa.Column('customer_feedback', sa.Text(), nullable=True),
        sa.Column('estimated_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('custom_fields', postgresql.JSONB(), nullable=True),
        sa.Column('auto_created', sa.Boolean(), nullable=False, default=False),
        sa.Column('monitoring_alert_id', sa.String(length=100), nullable=True),
        sa.Column('external_ticket_reference', sa.String(length=100), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sla_policy_id'], ['sla_policies.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['administrators.id']),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'])
    )
    op.create_index('ix_tickets_ticket_number', 'tickets', ['ticket_number'], unique=True)
    op.create_index('ix_tickets_status', 'tickets', ['status'])
    op.create_index('ix_tickets_priority', 'tickets', ['priority'])
    op.create_index('ix_tickets_customer_id', 'tickets', ['customer_id'])
    op.create_index('ix_tickets_assigned_to', 'tickets', ['assigned_to'])
    op.create_index('ix_tickets_created_at', 'tickets', ['created_at'])

    # Create ticket messages table
    op.create_table('ticket_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False, default='comment'),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('content_format', sa.String(length=20), nullable=False, default='text'),
        sa.Column('is_internal', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_solution', sa.Boolean(), nullable=False, default=False),
        sa.Column('author_type', sa.String(length=20), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('author_email', sa.String(length=255), nullable=True),
        sa.Column('is_auto_generated', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('sms_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('push_notification_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_message_id', sa.String(length=255), nullable=True),
        sa.Column('external_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE')
    )
    op.create_index('ix_ticket_messages_ticket_id', 'ticket_messages', ['ticket_id'])
    op.create_index('ix_ticket_messages_created_at', 'ticket_messages', ['created_at'])

    # Create ticket escalations table
    op.create_table('ticket_escalations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('escalation_reason', escalationreason_enum, nullable=False),
        sa.Column('escalation_level', sa.Integer(), nullable=False, default=1),
        sa.Column('escalated_from', sa.Integer(), nullable=True),
        sa.Column('escalated_to', sa.Integer(), nullable=False),
        sa.Column('escalated_from_team', sa.String(length=100), nullable=True),
        sa.Column('escalated_to_team', sa.String(length=100), nullable=True),
        sa.Column('escalation_notes', sa.Text(), nullable=True),
        sa.Column('urgency_justification', sa.Text(), nullable=True),
        sa.Column('response_notes', sa.Text(), nullable=True),
        sa.Column('response_action', sa.String(length=255), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('responded_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['escalated_from'], ['administrators.id']),
        sa.ForeignKeyConstraint(['escalated_to'], ['administrators.id']),
        sa.ForeignKeyConstraint(['responded_by'], ['administrators.id'])
    )
    op.create_index('ix_ticket_escalations_ticket_id', 'ticket_escalations', ['ticket_id'])

    # Create field work orders table
    op.create_table('field_work_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('work_order_number', sa.String(length=50), nullable=False),
        sa.Column('status', fieldworkstatus_enum, nullable=False, default='scheduled'),
        sa.Column('work_type', sa.String(length=100), nullable=False),
        sa.Column('work_description', sa.Text(), nullable=False),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('work_address', sa.String(length=500), nullable=False),
        sa.Column('gps_latitude', sa.String(length=20), nullable=True),
        sa.Column('gps_longitude', sa.String(length=20), nullable=True),
        sa.Column('location_contact_name', sa.String(length=255), nullable=True),
        sa.Column('location_contact_phone', sa.String(length=50), nullable=True),
        sa.Column('priority', ticketpriority_enum, nullable=False, default='normal'),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_duration_hours', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('assigned_technician', sa.Integer(), nullable=True),
        sa.Column('technician_team', sa.String(length=100), nullable=True),
        sa.Column('backup_technician', sa.Integer(), nullable=True),
        sa.Column('required_equipment', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('required_materials', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('equipment_assigned', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('customer_availability', sa.String(length=500), nullable=True),
        sa.Column('access_requirements', sa.String(length=500), nullable=True),
        sa.Column('safety_requirements', sa.String(length=500), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('work_performed', sa.Text(), nullable=True),
        sa.Column('findings', sa.Text(), nullable=True),
        sa.Column('work_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('customer_signature_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('customer_signature_obtained', sa.Boolean(), nullable=False, default=False),
        sa.Column('customer_satisfaction_score', sa.Integer(), nullable=True),
        sa.Column('before_photos', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('after_photos', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('work_photos', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('follow_up_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('follow_up_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_technician'], ['administrators.id']),
        sa.ForeignKeyConstraint(['backup_technician'], ['administrators.id'])
    )
    op.create_index('ix_field_work_orders_work_order_number', 'field_work_orders', ['work_order_number'], unique=True)
    op.create_index('ix_field_work_orders_status', 'field_work_orders', ['status'])
    op.create_index('ix_field_work_orders_assigned_technician', 'field_work_orders', ['assigned_technician'])

    # Create ticket time entries table
    op.create_table('ticket_time_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('hours_worked', sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column('work_description', sa.Text(), nullable=False),
        sa.Column('work_type', sa.String(length=100), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('worked_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worked_by'], ['administrators.id'])
    )
    op.create_index('ix_ticket_time_entries_ticket_id', 'ticket_time_entries', ['ticket_id'])

    # Create ticket status history table
    op.create_table('ticket_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_id', sa.Integer(), nullable=False),
        sa.Column('status', ticketstatus_enum, nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.String(length=500), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['administrators.id'])
    )
    op.create_index('ix_ticket_status_history_ticket_id', 'ticket_status_history', ['ticket_id'])

    # Create knowledge base articles table
    op.create_table('knowledge_base_articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_format', sa.String(length=20), nullable=False, default='html'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('ticket_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('service_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('difficulty_level', sa.String(length=50), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=True),
        sa.Column('reviewer_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='draft'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('helpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('not_helpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('version', sa.String(length=20), nullable=False, default='1.0'),
        sa.Column('previous_version_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['author_id'], ['administrators.id']),
        sa.ForeignKeyConstraint(['reviewer_id'], ['administrators.id']),
        sa.ForeignKeyConstraint(['previous_version_id'], ['knowledge_base_articles.id'])
    )
    op.create_index('ix_knowledge_base_articles_title', 'knowledge_base_articles', ['title'])
    op.create_index('ix_knowledge_base_articles_category', 'knowledge_base_articles', ['category'])
    op.create_index('ix_knowledge_base_articles_status', 'knowledge_base_articles', ['status'])

    # Create network incidents table
    op.create_table('network_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('incident_number', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('incident_type', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False, default='medium'),
        sa.Column('status', sa.String(length=50), nullable=False, default='open'),
        sa.Column('affected_devices', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('affected_networks', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('affected_services', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('affected_locations', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('impact_radius_km', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('estimated_customers_affected', sa.Integer(), nullable=False, default=0),
        sa.Column('confirmed_customers_affected', sa.Integer(), nullable=False, default=0),
        sa.Column('business_customers_affected', sa.Integer(), nullable=False, default=0),
        sa.Column('residential_customers_affected', sa.Integer(), nullable=False, default=0),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('incident_commander', sa.Integer(), nullable=True),
        sa.Column('response_team', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('corrective_actions', sa.Text(), nullable=True),
        sa.Column('preventive_actions', sa.Text(), nullable=True),
        sa.Column('customer_notification_sent', sa.Boolean(), nullable=False, default=False),
        sa.Column('status_page_updated', sa.Boolean(), nullable=False, default=False),
        sa.Column('vendor_ticket_numbers', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('monitoring_alert_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['incident_commander'], ['administrators.id'])
    )
    op.create_index('ix_network_incidents_incident_number', 'network_incidents', ['incident_number'], unique=True)
    op.create_index('ix_network_incidents_status', 'network_incidents', ['status'])
    op.create_index('ix_network_incidents_severity', 'network_incidents', ['severity'])

    # Create ticket templates table
    op.create_table('ticket_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ticket_type', tickettype_enum, nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('priority', ticketpriority_enum, nullable=False, default='normal'),
        sa.Column('title_template', sa.String(length=500), nullable=True),
        sa.Column('description_template', sa.Text(), nullable=True),
        sa.Column('auto_assign_team', sa.String(length=100), nullable=True),
        sa.Column('auto_assign_agent', sa.Integer(), nullable=True),
        sa.Column('sla_policy_id', sa.Integer(), nullable=True),
        sa.Column('require_customer_info', sa.Boolean(), nullable=False, default=True),
        sa.Column('require_service_info', sa.Boolean(), nullable=False, default=False),
        sa.Column('require_location_info', sa.Boolean(), nullable=False, default=False),
        sa.Column('custom_fields_required', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('default_custom_fields', postgresql.JSONB(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['auto_assign_agent'], ['administrators.id']),
        sa.ForeignKeyConstraint(['sla_policy_id'], ['sla_policies.id'])
    )
    op.create_index('ix_ticket_templates_name', 'ticket_templates', ['name'])
    op.create_index('ix_ticket_templates_ticket_type', 'ticket_templates', ['ticket_type'])

    # Insert default SLA policy
    op.execute("""
        INSERT INTO sla_policies (
            name, description, first_response_time, critical_resolution_time,
            urgent_resolution_time, high_resolution_time, normal_resolution_time,
            low_resolution_time, business_days, is_default
        ) VALUES (
            'Default SLA Policy', 'Standard SLA policy for all ticket types',
            60, 240, 480, 1440, 2880, 5760, ARRAY[1,2,3,4,5], true
        )
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('ticket_templates')
    op.drop_table('network_incidents')
    op.drop_table('knowledge_base_articles')
    op.drop_table('ticket_status_history')
    op.drop_table('ticket_time_entries')
    op.drop_table('field_work_orders')
    op.drop_table('ticket_escalations')
    op.drop_table('ticket_messages')
    op.drop_table('tickets')
    op.drop_table('sla_policies')
    
    # Drop enum types
    postgresql.ENUM(name='tickettemplate').drop(op.get_bind())
    postgresql.ENUM(name='fieldworkstatus').drop(op.get_bind())
    postgresql.ENUM(name='escalationreason').drop(op.get_bind())
    postgresql.ENUM(name='ticketsource').drop(op.get_bind())
    postgresql.ENUM(name='ticketstatus').drop(op.get_bind())
    postgresql.ENUM(name='ticketpriority').drop(op.get_bind())
    postgresql.ENUM(name='tickettype').drop(op.get_bind())
