"""Create settings and feature flags tables

Revision ID: settings_001
Revises: audit_logs_001
Create Date: 2025-01-26 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'settings_001'
down_revision = 'audit_logs_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create settings table
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('setting_type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=False),
        sa.Column('is_readonly', sa.Boolean(), nullable=False),
        sa.Column('validation_regex', sa.String(length=500), nullable=True),
        sa.Column('min_value', sa.String(length=50), nullable=True),
        sa.Column('max_value', sa.String(length=50), nullable=True),
        sa.Column('allowed_values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('requires_restart', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['administrators.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for settings
    op.create_index('ix_settings_key', 'settings', ['key'], unique=True)
    op.create_index('ix_settings_category_active', 'settings', ['category', 'is_active'])
    op.create_index('ix_settings_type_category', 'settings', ['setting_type', 'category'])
    
    # Create setting_history table
    op.create_table('setting_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('setting_id', sa.Integer(), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('changed_by_id', sa.Integer(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('change_reason', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for setting_history
    op.create_index('ix_setting_history_setting_id', 'setting_history', ['setting_id'])
    op.create_index('ix_setting_history_changed_at', 'setting_history', ['changed_at'])
    
    # Create feature_flags table
    op.create_table('feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('enabled_for_all', sa.Boolean(), nullable=False),
        sa.Column('enabled_percentage', sa.Integer(), nullable=False),
        sa.Column('enabled_user_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('enabled_ip_ranges', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('enabled_environments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rollout_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rollout_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('depends_on_flags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['administrators.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for feature_flags
    op.create_index('ix_feature_flags_name', 'feature_flags', ['name'], unique=True)
    op.create_index('ix_feature_flags_enabled', 'feature_flags', ['is_enabled'])
    op.create_index('ix_feature_flags_category', 'feature_flags', ['category'])
    
    # Create configuration_templates table
    op.create_table('configuration_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('template_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['administrators.id'], ),
        sa.ForeignKeyConstraint(['updated_by_id'], ['administrators.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for configuration_templates
    op.create_index('ix_configuration_templates_name', 'configuration_templates', ['name'], unique=True)
    op.create_index('ix_configuration_templates_category', 'configuration_templates', ['category'])


def downgrade():
    # Drop tables in reverse order
    op.drop_index('ix_configuration_templates_category', table_name='configuration_templates')
    op.drop_index('ix_configuration_templates_name', table_name='configuration_templates')
    op.drop_table('configuration_templates')
    
    op.drop_index('ix_feature_flags_category', table_name='feature_flags')
    op.drop_index('ix_feature_flags_enabled', table_name='feature_flags')
    op.drop_index('ix_feature_flags_name', table_name='feature_flags')
    op.drop_table('feature_flags')
    
    op.drop_index('ix_setting_history_changed_at', table_name='setting_history')
    op.drop_index('ix_setting_history_setting_id', table_name='setting_history')
    op.drop_table('setting_history')
    
    op.drop_index('ix_settings_type_category', table_name='settings')
    op.drop_index('ix_settings_category_active', table_name='settings')
    op.drop_index('ix_settings_key', table_name='settings')
    op.drop_table('settings')
