"""Create plugin system tables

Revision ID: create_plugin_system_tables
Revises: 
Create Date: 2025-01-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_plugin_system_tables'
down_revision = '0016_create_file_storage_tables'  # Current head revision
branch_labels = None
depends_on = None


def upgrade():
    # Check and create plugin enums only if they don't exist
    connection = op.get_bind()
    
    # Check if enums exist
    result = connection.execute(sa.text(
        "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname IN ('pluginstatus', 'plugintype', 'pluginpriority')"
    ))
    existing_enums = {row[0] for row in result}
    
    # Create plugin status enum if not exists
    if 'pluginstatus' not in existing_enums:
        plugin_status_enum = postgresql.ENUM(
            'INACTIVE', 'LOADING', 'ACTIVE', 'ERROR', 'DISABLED',
            name='pluginstatus'
        )
        plugin_status_enum.create(connection)
    
    # Create plugin type enum if not exists
    if 'plugintype' not in existing_enums:
        plugin_type_enum = postgresql.ENUM(
            'COMMUNICATION', 'BILLING', 'NETWORKING', 'AUTHENTICATION', 
            'MONITORING', 'INTEGRATION', 'UTILITY', 'CUSTOM',
            name='plugintype'
        )
        plugin_type_enum.create(connection)
    
    # Create plugin priority enum if not exists
    if 'pluginpriority' not in existing_enums:
        plugin_priority_enum = postgresql.ENUM(
            'CRITICAL', 'HIGH', 'NORMAL', 'LOW',
            name='pluginpriority'
        )
        plugin_priority_enum.create(connection)
    
    # Use existing or newly created enums for table creation
    plugin_status_enum = postgresql.ENUM(
        'INACTIVE', 'LOADING', 'ACTIVE', 'ERROR', 'DISABLED',
        name='pluginstatus'
    )
    plugin_type_enum = postgresql.ENUM(
        'COMMUNICATION', 'BILLING', 'NETWORKING', 'AUTHENTICATION', 
        'MONITORING', 'INTEGRATION', 'UTILITY', 'CUSTOM',
        name='plugintype'
    )
    plugin_priority_enum = postgresql.ENUM(
        'CRITICAL', 'HIGH', 'NORMAL', 'LOW',
        name='pluginpriority'
    )
    
    # Create plugins table
    op.create_table(
        'plugins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('license', sa.String(length=100), nullable=True),
        sa.Column('homepage', sa.String(length=500), nullable=True),
        sa.Column('plugin_type', plugin_type_enum, nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('priority', plugin_priority_enum, nullable=False, default='NORMAL'),
        sa.Column('status', plugin_status_enum, nullable=False, default='INACTIVE'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False),
        sa.Column('module_path', sa.String(length=500), nullable=False),
        sa.Column('entry_point', sa.String(length=255), nullable=False),
        sa.Column('config_schema', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('requirements', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('supported_versions', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('api_version', sa.String(length=20), nullable=False, default='1.0'),
        sa.Column('installed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_loaded', sa.DateTime(timezone=True), nullable=True),
        sa.Column('installed_by', sa.Integer(), nullable=True),
        sa.Column('load_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['installed_by'], ['administrators.id'], ondelete='SET NULL')
    )
    
    # Create plugin_configurations table
    op.create_table(
        'plugin_configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plugin_id', sa.Integer(), nullable=False),
        sa.Column('config_key', sa.String(length=255), nullable=False),
        sa.Column('config_value', postgresql.JSONB(), nullable=True),
        sa.Column('config_type', sa.String(length=50), nullable=False, default='string'),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_value', postgresql.JSONB(), nullable=True),
        sa.Column('validation_rules', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plugin_id', 'config_key'),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugins.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by'], ['administrators.id'], ondelete='SET NULL')
    )
    
    # Create plugin_hooks table
    op.create_table(
        'plugin_hooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plugin_id', sa.Integer(), nullable=False),
        sa.Column('hook_name', sa.String(length=255), nullable=False),
        sa.Column('hook_type', sa.String(length=50), nullable=False),
        sa.Column('callback_method', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, default=100),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parameters', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('return_type', sa.String(length=100), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_executed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('average_execution_time', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plugin_id', 'hook_name', 'callback_method'),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugins.id'], ondelete='CASCADE')
    )
    
    # Create plugin_dependencies table
    op.create_table(
        'plugin_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plugin_id', sa.Integer(), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=False),
        sa.Column('dependency_name', sa.String(length=255), nullable=False),
        sa.Column('version_constraint', sa.String(length=100), nullable=True),
        sa.Column('is_optional', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_satisfied', sa.Boolean(), nullable=False, default=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('install_command', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plugin_id', 'dependency_type', 'dependency_name'),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugins.id'], ondelete='CASCADE')
    )
    
    # Create plugin_logs table
    op.create_table(
        'plugin_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plugin_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('log_level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('context', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('hook_name', sa.String(length=255), nullable=True),
        sa.Column('execution_time', sa.Integer(), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['plugin_id'], ['plugins.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['administrators.id'], ondelete='SET NULL')
    )
    
    # Create plugin_registry table
    op.create_table(
        'plugin_registry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plugin_type', plugin_type_enum, nullable=False),
        sa.Column('latest_version', sa.String(length=50), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('license', sa.String(length=100), nullable=True),
        sa.Column('repository_url', sa.String(length=500), nullable=True),
        sa.Column('download_url', sa.String(length=500), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('requirements', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('supported_versions', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('screenshots', postgresql.ARRAY(sa.String()), nullable=True, default=[]),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_deprecated', sa.Boolean(), nullable=False, default=False),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('rating', sa.Integer(), nullable=False, default=0),
        sa.Column('review_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create plugin_templates table
    op.create_table(
        'plugin_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plugin_type', plugin_type_enum, nullable=False),
        sa.Column('template_version', sa.String(length=50), nullable=False),
        sa.Column('template_files', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('config_schema', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('documentation', sa.Text(), nullable=True),
        sa.Column('example_usage', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, default=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['created_by'], ['administrators.id'], ondelete='SET NULL')
    )
    
    # Create indexes for better performance
    op.create_index('idx_plugins_name', 'plugins', ['name'])
    op.create_index('idx_plugins_type', 'plugins', ['plugin_type'])
    op.create_index('idx_plugins_status', 'plugins', ['status'])
    op.create_index('idx_plugins_enabled', 'plugins', ['is_enabled'])
    op.create_index('idx_plugins_system', 'plugins', ['is_system'])
    op.create_index('idx_plugins_category', 'plugins', ['category'])
    
    op.create_index('idx_plugin_configurations_plugin_id', 'plugin_configurations', ['plugin_id'])
    op.create_index('idx_plugin_configurations_key', 'plugin_configurations', ['config_key'])
    
    op.create_index('idx_plugin_hooks_plugin_id', 'plugin_hooks', ['plugin_id'])
    op.create_index('idx_plugin_hooks_name', 'plugin_hooks', ['hook_name'])
    op.create_index('idx_plugin_hooks_type', 'plugin_hooks', ['hook_type'])
    op.create_index('idx_plugin_hooks_active', 'plugin_hooks', ['is_active'])
    
    op.create_index('idx_plugin_dependencies_plugin_id', 'plugin_dependencies', ['plugin_id'])
    op.create_index('idx_plugin_dependencies_type', 'plugin_dependencies', ['dependency_type'])
    op.create_index('idx_plugin_dependencies_name', 'plugin_dependencies', ['dependency_name'])
    
    op.create_index('idx_plugin_logs_plugin_id', 'plugin_logs', ['plugin_id'])
    op.create_index('idx_plugin_logs_level', 'plugin_logs', ['log_level'])
    op.create_index('idx_plugin_logs_created_at', 'plugin_logs', ['created_at'])
    op.create_index('idx_plugin_logs_hook_name', 'plugin_logs', ['hook_name'])
    
    op.create_index('idx_plugin_registry_name', 'plugin_registry', ['name'])
    op.create_index('idx_plugin_registry_type', 'plugin_registry', ['plugin_type'])
    op.create_index('idx_plugin_registry_verified', 'plugin_registry', ['is_verified'])
    op.create_index('idx_plugin_registry_featured', 'plugin_registry', ['is_featured'])
    
    op.create_index('idx_plugin_templates_name', 'plugin_templates', ['name'])
    op.create_index('idx_plugin_templates_type', 'plugin_templates', ['plugin_type'])
    op.create_index('idx_plugin_templates_active', 'plugin_templates', ['is_active'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_plugin_templates_active', table_name='plugin_templates')
    op.drop_index('idx_plugin_templates_type', table_name='plugin_templates')
    op.drop_index('idx_plugin_templates_name', table_name='plugin_templates')
    
    op.drop_index('idx_plugin_registry_featured', table_name='plugin_registry')
    op.drop_index('idx_plugin_registry_verified', table_name='plugin_registry')
    op.drop_index('idx_plugin_registry_type', table_name='plugin_registry')
    op.drop_index('idx_plugin_registry_name', table_name='plugin_registry')
    
    op.drop_index('idx_plugin_logs_hook_name', table_name='plugin_logs')
    op.drop_index('idx_plugin_logs_created_at', table_name='plugin_logs')
    op.drop_index('idx_plugin_logs_level', table_name='plugin_logs')
    op.drop_index('idx_plugin_logs_plugin_id', table_name='plugin_logs')
    
    op.drop_index('idx_plugin_dependencies_name', table_name='plugin_dependencies')
    op.drop_index('idx_plugin_dependencies_type', table_name='plugin_dependencies')
    op.drop_index('idx_plugin_dependencies_plugin_id', table_name='plugin_dependencies')
    
    op.drop_index('idx_plugin_hooks_active', table_name='plugin_hooks')
    op.drop_index('idx_plugin_hooks_type', table_name='plugin_hooks')
    op.drop_index('idx_plugin_hooks_name', table_name='plugin_hooks')
    op.drop_index('idx_plugin_hooks_plugin_id', table_name='plugin_hooks')
    
    op.drop_index('idx_plugin_configurations_key', table_name='plugin_configurations')
    op.drop_index('idx_plugin_configurations_plugin_id', table_name='plugin_configurations')
    
    op.drop_index('idx_plugins_category', table_name='plugins')
    op.drop_index('idx_plugins_system', table_name='plugins')
    op.drop_index('idx_plugins_enabled', table_name='plugins')
    op.drop_index('idx_plugins_status', table_name='plugins')
    op.drop_index('idx_plugins_type', table_name='plugins')
    op.drop_index('idx_plugins_name', table_name='plugins')
    
    # Drop tables
    op.drop_table('plugin_templates')
    op.drop_table('plugin_registry')
    op.drop_table('plugin_logs')
    op.drop_table('plugin_dependencies')
    op.drop_table('plugin_hooks')
    op.drop_table('plugin_configurations')
    op.drop_table('plugins')
    
    # Drop enums
    op.execute('DROP TYPE pluginpriority')
    op.execute('DROP TYPE plugintype')
    op.execute('DROP TYPE pluginstatus')
