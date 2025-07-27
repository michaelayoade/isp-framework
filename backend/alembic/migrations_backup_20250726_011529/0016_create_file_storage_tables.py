"""
Create file storage tables for MinIO S3 integration

Revision ID: 0016_create_file_storage_tables
Revises: 0015_add_portal_id_system
Create Date: 2025-07-25 22:51:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0016_create_file_storage_tables'
down_revision = '2025_07_23_add_api_management'
branch_labels = None
depends_on = None

# Define enum types
delete_status = sa.Enum('UPLOADED', 'PROCESSING', 'PROCESSED', 'FAILED', 'DELETED', name='filestatus')
import_status = sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', name='importstatus')
file_category = sa.Enum('CUSTOMER_DOCUMENT', 'TICKET_ATTACHMENT', 'CUSTOMER_IMPORT', 'SERVICE_EXPORT', 'CONFIG_BACKUP', 'SYSTEM_FILE', name='filecategory')


def upgrade():
    # Create enum types
    delete_status.create(op.get_bind())
    import_status.create(op.get_bind())
    file_category.create(op.get_bind())
    
    # Create file_metadata table
    op.create_table(
        'file_metadata',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_category', file_category, nullable=False),
        sa.Column('file_status', delete_status, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('ticket_id', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('bucket_name', sa.String(length=100), nullable=False),
        sa.Column('object_key', sa.String(length=500), nullable=False),
        sa.Column('presigned_url', sa.String(length=1000), nullable=True),
        sa.Column('url_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['administrators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_path'),
        sa.Index('ix_file_metadata_customer_id', 'customer_id'),
        sa.Index('ix_file_metadata_ticket_id', 'ticket_id'),
        sa.Index('ix_file_metadata_uploaded_by', 'uploaded_by'),
        sa.Index('ix_file_metadata_file_category', 'file_category'),
        sa.Index('ix_file_metadata_file_status', 'file_status'),
        sa.Index('ix_file_metadata_created_at', 'created_at')
    )
    
    # Create import_jobs table
    op.create_table(
        'import_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('file_metadata_id', sa.Integer(), nullable=False),
        sa.Column('import_type', sa.String(length=50), nullable=False),
        sa.Column('status', import_status, nullable=False),
        sa.Column('progress_percent', sa.Integer(), nullable=False, default=0),
        sa.Column('total_records', sa.Integer(), nullable=False, default=0),
        sa.Column('processed_records', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_records', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('validation_errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=[]),
        sa.Column('import_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['file_metadata_id'], ['file_metadata.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_import_jobs_file_metadata_id', 'file_metadata_id'),
        sa.Index('ix_import_jobs_status', 'status'),
        sa.Index('ix_import_jobs_created_by', 'created_by'),
        sa.Index('ix_import_jobs_created_at', 'created_at')
    )
    
    # Create export_jobs table
    op.create_table(
        'export_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_name', sa.String(length=255), nullable=False),
        sa.Column('export_type', sa.String(length=50), nullable=False),
        sa.Column('export_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default={}),
        sa.Column('file_format', sa.String(length=10), nullable=False, default='csv'),
        sa.Column('status', import_status, nullable=False),
        sa.Column('progress_percent', sa.Integer(), nullable=False, default=0),
        sa.Column('total_records', sa.Integer(), nullable=False, default=0),
        sa.Column('processed_records', sa.Integer(), nullable=False, default=0),
        sa.Column('output_file_metadata_id', sa.Integer(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['output_file_metadata_id'], ['file_metadata.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_export_jobs_output_file_metadata_id', 'output_file_metadata_id'),
        sa.Index('ix_export_jobs_status', 'status'),
        sa.Index('ix_export_jobs_created_by', 'created_by'),
        sa.Index('ix_export_jobs_created_at', 'created_at')
    )
    
    # Create file_permissions table
    op.create_table(
        'file_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_metadata_id', sa.Integer(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('allowed_customers', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=[]),
        sa.Column('allowed_roles', postgresql.JSONB(astext_type=sa.Text()), nullable=True, default=[]),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['file_metadata_id'], ['file_metadata.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_file_permissions_file_metadata_id', 'file_metadata_id'),
        sa.Index('ix_file_permissions_is_public', 'is_public'),
        sa.Index('ix_file_permissions_expires_at', 'expires_at')
    )
    
    # Add file relationships to existing tables
    op.add_column('customers', sa.Column('files', sa.ARRAY(sa.Integer()), nullable=True, default=[]))
    op.add_column('tickets', sa.Column('attachments', sa.ARRAY(sa.Integer()), nullable=True, default=[]))


def downgrade():
    # Drop tables
    op.drop_table('file_permissions')
    op.drop_table('export_jobs')
    op.drop_table('import_jobs')
    op.drop_table('file_metadata')
    
    # Drop enum types
    file_category.drop(op.get_bind())
    import_status.drop(op.get_bind())
    delete_status.drop(op.get_bind())
    
    # Remove file relationships from existing tables
    op.drop_column('customers', 'files')
    op.drop_column('tickets', 'attachments')
