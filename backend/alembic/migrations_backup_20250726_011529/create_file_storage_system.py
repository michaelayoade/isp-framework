"""
Create file storage system for MinIO S3 integration

Revision ID: 20240723_create_file_storage
Revises: create_ticketing_system
Create Date: 2024-07-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240723_create_file_storage'
down_revision = 'create_ticketing_system'
branch_labels = None
depends_on = None


def upgrade():
    # Create file storage tables
    op.create_table(
        'file_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('bucket_name', sa.String(length=100), nullable=False),
        sa.Column('object_key', sa.String(length=500), nullable=False),
        sa.Column('upload_status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('service_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['customer_services.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['administrators.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'background_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('queue_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['administrators.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'csv_imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_upload_id', sa.Integer(), nullable=False),
        sa.Column('import_type', sa.String(length=50), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=False),
        sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mapping_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['administrators.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['file_upload_id'], ['file_uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('idx_file_uploads_type', 'file_uploads', ['file_type'])
    op.create_index('idx_file_uploads_status', 'file_uploads', ['upload_status'])
    op.create_index('idx_file_uploads_customer', 'file_uploads', ['customer_id'])
    op.create_index('idx_file_uploads_ticket', 'file_uploads', ['ticket_id'])
    op.create_index('idx_file_uploads_created', 'file_uploads', ['created_at'])
    op.create_index('idx_file_uploads_expires', 'file_uploads', ['expires_at'])

    op.create_index('idx_background_jobs_queue', 'background_jobs', ['queue_name'])
    op.create_index('idx_background_jobs_status', 'background_jobs', ['status'])
    op.create_index('idx_background_jobs_priority', 'background_jobs', ['priority'])
    op.create_index('idx_background_jobs_created', 'background_jobs', ['created_at'])

    op.create_index('idx_csv_imports_status', 'csv_imports', ['status'])
    op.create_index('idx_csv_imports_type', 'csv_imports', ['import_type'])
    op.create_index('idx_csv_imports_file', 'csv_imports', ['file_upload_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_csv_imports_file', table_name='csv_imports')
    op.drop_index('idx_csv_imports_type', table_name='csv_imports')
    op.drop_index('idx_csv_imports_status', table_name='csv_imports')

    op.drop_index('idx_background_jobs_created', table_name='background_jobs')
    op.drop_index('idx_background_jobs_priority', table_name='background_jobs')
    op.drop_index('idx_background_jobs_status', table_name='background_jobs')
    op.drop_index('idx_background_jobs_queue', table_name='background_jobs')

    op.drop_index('idx_file_uploads_expires', table_name='file_uploads')
    op.drop_index('idx_file_uploads_created', table_name='file_uploads')
    op.drop_index('idx_file_uploads_ticket', table_name='file_uploads')
    op.drop_index('idx_file_uploads_customer', table_name='file_uploads')
    op.drop_index('idx_file_uploads_status', table_name='file_uploads')
    op.drop_index('idx_file_uploads_type', table_name='file_uploads')

    # Drop tables
    op.drop_table('csv_imports')
    op.drop_table('background_jobs')
    op.drop_table('file_uploads')
