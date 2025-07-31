"""Create ticket statuses lookup table

Revision ID: 20250730_create_ticket_statuses
Revises: 20250730_create_service_types
Create Date: 2025-07-30 07:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_ticket_statuses'
down_revision = '20250730_create_service_types'
branch_labels = None
depends_on = None


def upgrade():
    # Create ticket_statuses table
    op.create_table('ticket_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_initial', sa.Boolean(), nullable=True),
        sa.Column('is_final', sa.Boolean(), nullable=True),
        sa.Column('requires_assignment', sa.Boolean(), nullable=True),
        sa.Column('auto_close_after_days', sa.Integer(), nullable=True),
        sa.Column('is_customer_visible', sa.Boolean(), nullable=True),
        sa.Column('customer_description', sa.String(length=255), nullable=True),
        sa.Column('pauses_sla', sa.Boolean(), nullable=True),
        sa.Column('escalation_hours', sa.Integer(), nullable=True),
        sa.Column('color_hex', sa.String(length=7), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ticket_statuses_id'), 'ticket_statuses', ['id'], unique=False)
    op.create_index(op.f('ix_ticket_statuses_code'), 'ticket_statuses', ['code'], unique=True)
    
    # Insert default ticket statuses
    ticket_statuses_table = sa.table('ticket_statuses',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('is_initial', sa.Boolean),
        sa.column('is_final', sa.Boolean),
        sa.column('requires_assignment', sa.Boolean),
        sa.column('auto_close_after_days', sa.Integer),
        sa.column('is_customer_visible', sa.Boolean),
        sa.column('customer_description', sa.String),
        sa.column('pauses_sla', sa.Boolean),
        sa.column('escalation_hours', sa.Integer),
        sa.column('color_hex', sa.String),
        sa.column('icon_name', sa.String)
    )
    
    op.bulk_insert(ticket_statuses_table, [
        {
            'code': 'open',
            'name': 'Open',
            'description': 'New ticket awaiting initial review',
            'is_active': True,
            'is_system': True,
            'sort_order': 1,
            'is_initial': True,
            'is_final': False,
            'requires_assignment': False,
            'auto_close_after_days': None,
            'is_customer_visible': True,
            'customer_description': 'Your ticket has been received and is awaiting review',
            'pauses_sla': False,
            'escalation_hours': 24,
            'color_hex': '#3B82F6',  # Blue
            'icon_name': 'mail'
        },
        {
            'code': 'assigned',
            'name': 'Assigned',
            'description': 'Ticket assigned to a technician',
            'is_active': True,
            'is_system': True,
            'sort_order': 2,
            'is_initial': False,
            'is_final': False,
            'requires_assignment': True,
            'auto_close_after_days': None,
            'is_customer_visible': True,
            'customer_description': 'Your ticket has been assigned to a technician',
            'pauses_sla': False,
            'escalation_hours': 48,
            'color_hex': '#F59E0B',  # Amber
            'icon_name': 'user-check'
        },
        {
            'code': 'in_progress',
            'name': 'In Progress',
            'description': 'Technician is actively working on the ticket',
            'is_active': True,
            'is_system': True,
            'sort_order': 3,
            'is_initial': False,
            'is_final': False,
            'requires_assignment': True,
            'auto_close_after_days': None,
            'is_customer_visible': True,
            'customer_description': 'We are actively working on your issue',
            'pauses_sla': False,
            'escalation_hours': 72,
            'color_hex': '#8B5CF6',  # Purple
            'icon_name': 'cog'
        },
        {
            'code': 'pending_customer',
            'name': 'Pending Customer Response',
            'description': 'Waiting for customer to provide information or take action',
            'is_active': True,
            'is_system': True,
            'sort_order': 4,
            'is_initial': False,
            'is_final': False,
            'requires_assignment': False,
            'auto_close_after_days': 7,
            'is_customer_visible': True,
            'customer_description': 'We need additional information from you to proceed',
            'pauses_sla': True,
            'escalation_hours': None,
            'color_hex': '#F97316',  # Orange
            'icon_name': 'clock'
        },
        {
            'code': 'resolved',
            'name': 'Resolved',
            'description': 'Issue has been resolved, awaiting customer confirmation',
            'is_active': True,
            'is_system': True,
            'sort_order': 5,
            'is_initial': False,
            'is_final': False,
            'requires_assignment': False,
            'auto_close_after_days': 3,
            'is_customer_visible': True,
            'customer_description': 'Your issue has been resolved. Please confirm if you need further assistance',
            'pauses_sla': True,
            'escalation_hours': None,
            'color_hex': '#10B981',  # Green
            'icon_name': 'check-circle'
        },
        {
            'code': 'closed',
            'name': 'Closed',
            'description': 'Ticket completed and closed',
            'is_active': True,
            'is_system': True,
            'sort_order': 6,
            'is_initial': False,
            'is_final': True,
            'requires_assignment': False,
            'auto_close_after_days': None,
            'is_customer_visible': True,
            'customer_description': 'Your ticket has been completed and closed',
            'pauses_sla': True,
            'escalation_hours': None,
            'color_hex': '#6B7280',  # Gray
            'icon_name': 'x-circle'
        },
        {
            'code': 'cancelled',
            'name': 'Cancelled',
            'description': 'Ticket cancelled by customer or system',
            'is_active': True,
            'is_system': True,
            'sort_order': 7,
            'is_initial': False,
            'is_final': True,
            'requires_assignment': False,
            'auto_close_after_days': None,
            'is_customer_visible': True,
            'customer_description': 'Your ticket has been cancelled',
            'pauses_sla': True,
            'escalation_hours': None,
            'color_hex': '#EF4444',  # Red
            'icon_name': 'minus-circle'
        },
        {
            'code': 'escalated',
            'name': 'Escalated',
            'description': 'Ticket escalated to higher support tier',
            'is_active': True,
            'is_system': False,
            'sort_order': 8,
            'is_initial': False,
            'is_final': False,
            'requires_assignment': True,
            'auto_close_after_days': None,
            'is_customer_visible': True,
            'customer_description': 'Your ticket has been escalated to our senior support team',
            'pauses_sla': False,
            'escalation_hours': 24,
            'color_hex': '#DC2626',  # Dark Red
            'icon_name': 'arrow-up'
        }
    ])
    
    # Add status_id column to tickets table if it exists
    try:
        op.add_column('tickets', sa.Column('status_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'tickets', 'ticket_statuses', ['status_id'], ['id'])
        
        # Migrate existing status enum values to status_id
        op.execute("""
            UPDATE tickets 
            SET status_id = (
                SELECT id FROM ticket_statuses 
                WHERE ticket_statuses.code = tickets.status::text
            )
            WHERE status::text IN ('open', 'assigned', 'in_progress', 'pending_customer', 'resolved', 'closed', 'cancelled', 'escalated')
        """)
        
        # Set default status_id to 'open' (id=1) for any remaining NULL values
        op.execute("UPDATE tickets SET status_id = 1 WHERE status_id IS NULL")
        
        # Make status_id NOT NULL after migration
        op.alter_column('tickets', 'status_id', nullable=False)
        
        # Drop the old status enum column
        op.drop_column('tickets', 'status')
    except Exception:
        # tickets table doesn't exist yet, skip this part
        pass


def downgrade():
    # Add back the status enum column to tickets if it exists
    try:
        # Create the enum type first
        ticket_status_enum = sa.Enum(
            'open', 'assigned', 'in_progress', 'pending_customer', 
            'resolved', 'closed', 'cancelled', 'escalated',
            name='ticketstatus'
        )
        ticket_status_enum.create(op.get_bind())
        
        op.add_column('tickets', sa.Column('status', ticket_status_enum, nullable=True))
        
        # Migrate status_id back to enum values
        op.execute("""
            UPDATE tickets 
            SET status = (
                SELECT code::ticketstatus FROM ticket_statuses 
                WHERE ticket_statuses.id = tickets.status_id
            )
        """)
        
        # Set default for any NULL values
        op.execute("UPDATE tickets SET status = 'open' WHERE status IS NULL")
        
        # Make status NOT NULL and drop foreign key
        op.alter_column('tickets', 'status', nullable=False)
        op.drop_constraint(None, 'tickets', type_='foreignkey')
        op.drop_column('tickets', 'status_id')
    except Exception:
        # tickets table doesn't exist, skip this part
        pass
    
    # Drop ticket_statuses table
    op.drop_index(op.f('ix_ticket_statuses_code'), table_name='ticket_statuses')
    op.drop_index(op.f('ix_ticket_statuses_id'), table_name='ticket_statuses')
    op.drop_table('ticket_statuses')
