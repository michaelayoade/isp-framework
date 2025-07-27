"""Enhanced Audit System with Soft Delete Support

Revision ID: 006_enhanced_audit_system
Revises: 005_add_portal_id_uniqueness
Create Date: 2025-07-26 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_enhanced_audit_system'
down_revision = '005_add_portal_id_uniqueness'
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced audit system tables and update existing models."""
    
    # Create enhanced audit logs table
    op.create_table('enhanced_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.String(length=50), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('old_values', sa.JSON(), nullable=True),
        sa.Column('new_values', sa.JSON(), nullable=True),
        sa.Column('changed_fields', sa.JSON(), nullable=True),
        sa.Column('field_count', sa.Integer(), nullable=True),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_type', sa.String(length=50), nullable=True),
        sa.Column('actor_name', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('business_reason', sa.String(length=500), nullable=True),
        sa.Column('compliance_category', sa.String(length=100), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('version_before', sa.Integer(), nullable=True),
        sa.Column('version_after', sa.Integer(), nullable=True),
        sa.Column('batch_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['actor_id'], ['administrators.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for enhanced audit logs
    op.create_index('idx_audit_table_record', 'enhanced_audit_logs', ['table_name', 'record_id'])
    op.create_index('idx_audit_timestamp_table', 'enhanced_audit_logs', ['timestamp', 'table_name'])
    op.create_index('idx_audit_actor_timestamp', 'enhanced_audit_logs', ['actor_id', 'timestamp'])
    op.create_index('idx_audit_operation_timestamp', 'enhanced_audit_logs', ['operation', 'timestamp'])
    op.create_index('idx_audit_compliance', 'enhanced_audit_logs', ['compliance_category', 'timestamp'])
    op.create_index('idx_audit_risk_level', 'enhanced_audit_logs', ['risk_level', 'timestamp'])
    op.create_index(op.f('ix_enhanced_audit_logs_id'), 'enhanced_audit_logs', ['id'])
    op.create_index(op.f('ix_enhanced_audit_logs_table_name'), 'enhanced_audit_logs', ['table_name'])
    op.create_index(op.f('ix_enhanced_audit_logs_record_id'), 'enhanced_audit_logs', ['record_id'])
    op.create_index(op.f('ix_enhanced_audit_logs_operation'), 'enhanced_audit_logs', ['operation'])
    op.create_index(op.f('ix_enhanced_audit_logs_actor_id'), 'enhanced_audit_logs', ['actor_id'])
    op.create_index(op.f('ix_enhanced_audit_logs_actor_type'), 'enhanced_audit_logs', ['actor_type'])
    op.create_index(op.f('ix_enhanced_audit_logs_ip_address'), 'enhanced_audit_logs', ['ip_address'])
    op.create_index(op.f('ix_enhanced_audit_logs_request_id'), 'enhanced_audit_logs', ['request_id'])
    op.create_index(op.f('ix_enhanced_audit_logs_session_id'), 'enhanced_audit_logs', ['session_id'])
    op.create_index(op.f('ix_enhanced_audit_logs_compliance_category'), 'enhanced_audit_logs', ['compliance_category'])
    op.create_index(op.f('ix_enhanced_audit_logs_risk_level'), 'enhanced_audit_logs', ['risk_level'])
    op.create_index(op.f('ix_enhanced_audit_logs_timestamp'), 'enhanced_audit_logs', ['timestamp'])
    op.create_index(op.f('ix_enhanced_audit_logs_batch_id'), 'enhanced_audit_logs', ['batch_id'])

    # Create configuration snapshots table
    op.create_table('configuration_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('snapshot_name', sa.String(length=255), nullable=False),
        sa.Column('snapshot_type', sa.String(length=50), nullable=False),
        sa.Column('configuration_data', sa.JSON(), nullable=False),
        sa.Column('configuration_hash', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('previous_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['previous_snapshot_id'], ['configuration_snapshots.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for configuration snapshots
    op.create_index('idx_config_snapshot_type_date', 'configuration_snapshots', ['snapshot_type', 'created_at'])
    op.create_index('idx_config_snapshot_hash', 'configuration_snapshots', ['configuration_hash'])
    op.create_index('idx_config_snapshot_active', 'configuration_snapshots', ['is_active', 'created_at'])
    op.create_index(op.f('ix_configuration_snapshots_id'), 'configuration_snapshots', ['id'])
    op.create_index(op.f('ix_configuration_snapshots_snapshot_name'), 'configuration_snapshots', ['snapshot_name'])
    op.create_index(op.f('ix_configuration_snapshots_snapshot_type'), 'configuration_snapshots', ['snapshot_type'])
    op.create_index(op.f('ix_configuration_snapshots_configuration_hash'), 'configuration_snapshots', ['configuration_hash'])
    op.create_index(op.f('ix_configuration_snapshots_created_at'), 'configuration_snapshots', ['created_at'])
    op.create_index(op.f('ix_configuration_snapshots_is_active'), 'configuration_snapshots', ['is_active'])
    op.create_index(op.f('ix_configuration_snapshots_expires_at'), 'configuration_snapshots', ['expires_at'])

    # Create audit queue table
    op.create_table('audit_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.String(length=50), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('audit_data', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit queue
    op.create_index('idx_audit_queue_status_priority', 'audit_queue', ['status', 'priority', 'created_at'])
    op.create_index('idx_audit_queue_retry', 'audit_queue', ['next_retry_at', 'status'])
    op.create_index('idx_audit_queue_table_record', 'audit_queue', ['table_name', 'record_id'])
    op.create_index(op.f('ix_audit_queue_id'), 'audit_queue', ['id'])
    op.create_index(op.f('ix_audit_queue_table_name'), 'audit_queue', ['table_name'])
    op.create_index(op.f('ix_audit_queue_record_id'), 'audit_queue', ['record_id'])
    op.create_index(op.f('ix_audit_queue_status'), 'audit_queue', ['status'])
    op.create_index(op.f('ix_audit_queue_created_at'), 'audit_queue', ['created_at'])
    op.create_index(op.f('ix_audit_queue_next_retry_at'), 'audit_queue', ['next_retry_at'])
    op.create_index(op.f('ix_audit_queue_priority'), 'audit_queue', ['priority'])

    # Add soft delete columns to critical tables
    critical_tables = [
        'customers',
        'customer_billing_accounts',
        'invoices',
        'payments',
        'customer_services',
        'administrators',
        'tariffs'
    ]
    
    for table_name in critical_tables:
        # Check if table exists before adding columns
        inspector = sa.inspect(op.get_bind())
        if table_name in inspector.get_table_names():
            try:
                # Add soft delete columns
                op.add_column(table_name, sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
                op.add_column(table_name, sa.Column('deleted_by_id', sa.Integer(), nullable=True))
                op.add_column(table_name, sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
                op.add_column(table_name, sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
                
                # Add indexes for soft delete columns
                op.create_index(f'ix_{table_name}_deleted_at', table_name, ['deleted_at'])
                op.create_index(f'ix_{table_name}_is_deleted', table_name, ['is_deleted'])
                
                # Add foreign key for deleted_by_id
                op.create_foreign_key(f'fk_{table_name}_deleted_by', table_name, 'administrators', ['deleted_by_id'], ['id'])
                
            except Exception as e:
                # Log the error but continue with other tables
                print(f"Warning: Could not add soft delete columns to {table_name}: {e}")


def downgrade():
    """Remove enhanced audit system tables and columns."""
    
    # Remove soft delete columns from critical tables
    critical_tables = [
        'customers',
        'customer_billing_accounts', 
        'invoices',
        'payments',
        'customer_services',
        'administrators',
        'tariffs'
    ]
    
    for table_name in critical_tables:
        inspector = sa.inspect(op.get_bind())
        if table_name in inspector.get_table_names():
            try:
                # Drop foreign key constraint
                op.drop_constraint(f'fk_{table_name}_deleted_by', table_name, type_='foreignkey')
                
                # Drop indexes
                op.drop_index(f'ix_{table_name}_deleted_at', table_name)
                op.drop_index(f'ix_{table_name}_is_deleted', table_name)
                
                # Drop columns
                op.drop_column(table_name, 'version')
                op.drop_column(table_name, 'is_deleted')
                op.drop_column(table_name, 'deleted_by_id')
                op.drop_column(table_name, 'deleted_at')
                
            except Exception as e:
                print(f"Warning: Could not remove soft delete columns from {table_name}: {e}")
    
    # Drop audit queue table
    op.drop_index(op.f('ix_audit_queue_priority'), table_name='audit_queue')
    op.drop_index(op.f('ix_audit_queue_next_retry_at'), table_name='audit_queue')
    op.drop_index(op.f('ix_audit_queue_created_at'), table_name='audit_queue')
    op.drop_index(op.f('ix_audit_queue_status'), table_name='audit_queue')
    op.drop_index(op.f('ix_audit_queue_record_id'), table_name='audit_queue')
    op.drop_index(op.f('ix_audit_queue_table_name'), table_name='audit_queue')
    op.drop_index(op.f('ix_audit_queue_id'), table_name='audit_queue')
    op.drop_index('idx_audit_queue_table_record', table_name='audit_queue')
    op.drop_index('idx_audit_queue_retry', table_name='audit_queue')
    op.drop_index('idx_audit_queue_status_priority', table_name='audit_queue')
    op.drop_table('audit_queue')
    
    # Drop configuration snapshots table
    op.drop_index(op.f('ix_configuration_snapshots_expires_at'), table_name='configuration_snapshots')
    op.drop_index(op.f('ix_configuration_snapshots_is_active'), table_name='configuration_snapshots')
    op.drop_index(op.f('ix_configuration_snapshots_created_at'), table_name='configuration_snapshots')
    op.drop_index(op.f('ix_configuration_snapshots_configuration_hash'), table_name='configuration_snapshots')
    op.drop_index(op.f('ix_configuration_snapshots_snapshot_type'), table_name='configuration_snapshots')
    op.drop_index(op.f('ix_configuration_snapshots_snapshot_name'), table_name='configuration_snapshots')
    op.drop_index(op.f('ix_configuration_snapshots_id'), table_name='configuration_snapshots')
    op.drop_index('idx_config_snapshot_active', table_name='configuration_snapshots')
    op.drop_index('idx_config_snapshot_hash', table_name='configuration_snapshots')
    op.drop_index('idx_config_snapshot_type_date', table_name='configuration_snapshots')
    op.drop_table('configuration_snapshots')
    
    # Drop enhanced audit logs table
    op.drop_index(op.f('ix_enhanced_audit_logs_batch_id'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_timestamp'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_risk_level'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_compliance_category'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_session_id'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_request_id'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_ip_address'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_actor_type'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_actor_id'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_operation'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_record_id'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_table_name'), table_name='enhanced_audit_logs')
    op.drop_index(op.f('ix_enhanced_audit_logs_id'), table_name='enhanced_audit_logs')
    op.drop_index('idx_audit_risk_level', table_name='enhanced_audit_logs')
    op.drop_index('idx_audit_compliance', table_name='enhanced_audit_logs')
    op.drop_index('idx_audit_operation_timestamp', table_name='enhanced_audit_logs')
    op.drop_index('idx_audit_actor_timestamp', table_name='enhanced_audit_logs')
    op.drop_index('idx_audit_timestamp_table', table_name='enhanced_audit_logs')
    op.drop_index('idx_audit_table_record', table_name='enhanced_audit_logs')
    op.drop_table('enhanced_audit_logs')
