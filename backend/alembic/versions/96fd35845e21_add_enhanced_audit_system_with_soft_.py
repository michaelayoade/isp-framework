"""Add enhanced audit system with soft delete support

Revision ID: 96fd35845e21
Revises: merge_heads_20250726
Create Date: 2025-07-26 18:47:23.292576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96fd35845e21'
down_revision: Union[str, None] = 'merge_heads_20250726'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enhanced audit queue table
    op.create_table(
        'audit_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(20), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit queue
    op.create_index('idx_audit_queue_status', 'audit_queue', ['status'])
    op.create_index('idx_audit_queue_table_record', 'audit_queue', ['table_name', 'record_id'])
    op.create_index('idx_audit_queue_created_at', 'audit_queue', ['created_at'])
    
    # Add soft delete columns to critical tables
    tables_to_enhance = [
        'customers',
        'customers_extended', 
        'internet_services',
        'voice_services',
        'bundle_services',
        'billing_accounts',
        'invoices',
        'payments',
        'credit_notes',
        'tickets',
        'network_devices',
        'ip_pools',
        'ip_allocations',
        'resellers'
    ]
    
    for table_name in tables_to_enhance:
        # Check if table exists before adding columns
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        if table_name in inspector.get_table_names():
            # Add soft delete columns if they don't exist
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if 'deleted_at' not in existing_columns:
                op.add_column(table_name, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
            if 'deleted_by_id' not in existing_columns:
                op.add_column(table_name, sa.Column('deleted_by_id', sa.Integer(), nullable=True))
            if 'version' not in existing_columns:
                op.add_column(table_name, sa.Column('version', sa.Integer(), nullable=False, default=1))
    
    # Create configuration snapshots table
    op.create_table(
        'configuration_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('config_type', sa.String(50), nullable=False),
        sa.Column('config_key', sa.String(100), nullable=False),
        sa.Column('snapshot_data', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for configuration snapshots
    op.create_index('idx_config_snapshots_type_key', 'configuration_snapshots', ['config_type', 'config_key'])
    op.create_index('idx_config_snapshots_version', 'configuration_snapshots', ['version'])
    op.create_index('idx_config_snapshots_active', 'configuration_snapshots', ['is_active'])
    
    # Create change data capture log table
    op.create_table(
        'cdc_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.String(50), nullable=False),
        sa.Column('operation', sa.String(20), nullable=False),
        sa.Column('change_data', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('transaction_id', sa.String(100), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, default='application'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for CDC log
    op.create_index('idx_cdc_log_table_record', 'cdc_log', ['table_name', 'record_id'])
    op.create_index('idx_cdc_log_timestamp', 'cdc_log', ['timestamp'])
    op.create_index('idx_cdc_log_operation', 'cdc_log', ['operation'])
    
    # Create audit processing status table
    op.create_table(
        'audit_processing_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('processor_name', sa.String(100), nullable=False),
        sa.Column('last_processed_id', sa.Integer(), nullable=True),
        sa.Column('last_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index for processor names
    op.create_index('idx_audit_processor_name', 'audit_processing_status', ['processor_name'], unique=True)


def downgrade() -> None:
    # Drop audit processing status table
    op.drop_table('audit_processing_status')
    
    # Drop CDC log table
    op.drop_table('cdc_log')
    
    # Drop configuration snapshots table
    op.drop_table('configuration_snapshots')
    
    # Remove soft delete columns from enhanced tables
    tables_to_revert = [
        'customers',
        'customers_extended', 
        'internet_services',
        'voice_services',
        'bundle_services',
        'billing_accounts',
        'invoices',
        'payments',
        'credit_notes',
        'tickets',
        'network_devices',
        'ip_pools',
        'ip_allocations',
        'resellers'
    ]
    
    for table_name in tables_to_revert:
        # Check if table exists before removing columns
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        if table_name in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if 'version' in existing_columns:
                op.drop_column(table_name, 'version')
            if 'deleted_by_id' in existing_columns:
                op.drop_column(table_name, 'deleted_by_id')
            if 'deleted_at' in existing_columns:
                op.drop_column(table_name, 'deleted_at')
