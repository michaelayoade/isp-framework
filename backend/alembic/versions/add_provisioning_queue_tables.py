"""Add provisioning queue tables

Revision ID: add_provisioning_queue
Revises: settings_001
Create Date: 2025-01-29 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_provisioning_queue'
down_revision = 'settings_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create provisioning_jobs table
    op.create_table(
        'provisioning_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=255), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(length=50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_activate', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provisioning_jobs_customer_id'), 'provisioning_jobs', ['customer_id'], unique=False)
    op.create_index(op.f('ix_provisioning_jobs_id'), 'provisioning_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_provisioning_jobs_job_id'), 'provisioning_jobs', ['job_id'], unique=True)
    op.create_index(op.f('ix_provisioning_jobs_priority'), 'provisioning_jobs', ['priority'], unique=False)
    op.create_index(op.f('ix_provisioning_jobs_service_id'), 'provisioning_jobs', ['service_id'], unique=False)
    op.create_index(op.f('ix_provisioning_jobs_service_type'), 'provisioning_jobs', ['service_type'], unique=False)
    op.create_index(op.f('ix_provisioning_jobs_status'), 'provisioning_jobs', ['status'], unique=False)

    # Create provisioning_job_history table
    op.create_table(
        'provisioning_job_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('old_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['provisioning_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provisioning_job_history_id'), 'provisioning_job_history', ['id'], unique=False)
    op.create_index(op.f('ix_provisioning_job_history_job_id'), 'provisioning_job_history', ['job_id'], unique=False)

    # Create provisioning_worker_status table
    op.create_table(
        'provisioning_worker_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.String(length=255), nullable=True),
        sa.Column('worker_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('current_job_id', sa.String(length=255), nullable=True),
        sa.Column('jobs_processed', sa.Integer(), nullable=True),
        sa.Column('jobs_succeeded', sa.Integer(), nullable=True),
        sa.Column('jobs_failed', sa.Integer(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_job_started', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_job_completed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_concurrent_jobs', sa.Integer(), nullable=True),
        sa.Column('supported_service_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provisioning_worker_status_id'), 'provisioning_worker_status', ['id'], unique=False)
    op.create_index(op.f('ix_provisioning_worker_status_worker_id'), 'provisioning_worker_status', ['worker_id'], unique=True)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_provisioning_worker_status_worker_id'), table_name='provisioning_worker_status')
    op.drop_index(op.f('ix_provisioning_worker_status_id'), table_name='provisioning_worker_status')
    op.drop_table('provisioning_worker_status')
    
    op.drop_index(op.f('ix_provisioning_job_history_job_id'), table_name='provisioning_job_history')
    op.drop_index(op.f('ix_provisioning_job_history_id'), table_name='provisioning_job_history')
    op.drop_table('provisioning_job_history')
    
    op.drop_index(op.f('ix_provisioning_jobs_status'), table_name='provisioning_jobs')
    op.drop_index(op.f('ix_provisioning_jobs_service_type'), table_name='provisioning_jobs')
    op.drop_index(op.f('ix_provisioning_jobs_service_id'), table_name='provisioning_jobs')
    op.drop_index(op.f('ix_provisioning_jobs_priority'), table_name='provisioning_jobs')
    op.drop_index(op.f('ix_provisioning_jobs_job_id'), table_name='provisioning_jobs')
    op.drop_index(op.f('ix_provisioning_jobs_id'), table_name='provisioning_jobs')
    op.drop_index(op.f('ix_provisioning_jobs_customer_id'), table_name='provisioning_jobs')
    op.drop_table('provisioning_jobs')
