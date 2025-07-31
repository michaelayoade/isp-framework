"""create dead letter queue tables

Revision ID: create_dead_letter_queue_tables
Revises: 
Create Date: 2025-01-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_dead_letter_queue_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create dead letter queue and task execution log tables."""
    
    # Create dead_letter_queue table
    op.create_table(
        'dead_letter_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('queue_name', sa.String(length=100), nullable=False, server_default='default'),
        sa.Column('task_args', sa.Text(), nullable=True),
        sa.Column('task_kwargs', sa.Text(), nullable=True),
        sa.Column('exception_type', sa.String(length=255), nullable=True),
        sa.Column('exception_message', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requeued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for dead_letter_queue
    op.create_index('ix_dead_letter_queue_id', 'dead_letter_queue', ['id'])
    op.create_index('ix_dead_letter_queue_task_id', 'dead_letter_queue', ['task_id'])
    op.create_index('ix_dead_letter_queue_task_name', 'dead_letter_queue', ['task_name'])
    op.create_index('ix_dead_letter_queue_status', 'dead_letter_queue', ['status'])
    
    # Create task_execution_logs table
    op.create_table(
        'task_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('worker_name', sa.String(length=255), nullable=True),
        sa.Column('queue_name', sa.String(length=100), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for task_execution_logs
    op.create_index('ix_task_execution_logs_id', 'task_execution_logs', ['id'])
    op.create_index('ix_task_execution_logs_task_id', 'task_execution_logs', ['task_id'])
    op.create_index('ix_task_execution_logs_task_name', 'task_execution_logs', ['task_name'])
    op.create_index('ix_task_execution_logs_status', 'task_execution_logs', ['status'])


def downgrade():
    """Drop dead letter queue and task execution log tables."""
    
    # Drop indexes first
    op.drop_index('ix_task_execution_logs_status', 'task_execution_logs')
    op.drop_index('ix_task_execution_logs_task_name', 'task_execution_logs')
    op.drop_index('ix_task_execution_logs_task_id', 'task_execution_logs')
    op.drop_index('ix_task_execution_logs_id', 'task_execution_logs')
    
    op.drop_index('ix_dead_letter_queue_status', 'dead_letter_queue')
    op.drop_index('ix_dead_letter_queue_task_name', 'dead_letter_queue')
    op.drop_index('ix_dead_letter_queue_task_id', 'dead_letter_queue')
    op.drop_index('ix_dead_letter_queue_id', 'dead_letter_queue')
    
    # Drop tables
    op.drop_table('task_execution_logs')
    op.drop_table('dead_letter_queue')
