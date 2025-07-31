"""Add service management tables

Revision ID: 4db3f05bfae9
Revises: 00ba038d8a2e
Create Date: 2025-07-23 23:33:02.470790

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4db3f05bfae9'
down_revision: Union[str, None] = '00ba038d8a2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Attempt to create internet_services table if it does not yet exist
    try:
        op.create_table(
            'internet_services',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('download_speed', sa.Integer(), nullable=False),
            sa.Column('upload_speed', sa.Integer(), nullable=False),
            sa.Column('data_limit', sa.Integer(), nullable=True),
            sa.Column('monthly_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
            sa.Column('setup_fee', sa.DECIMAL(precision=10, scale=2), nullable=True),
            sa.Column('cancellation_fee', sa.DECIMAL(precision=10, scale=2), nullable=True),
            sa.Column('router_id', sa.Integer(), nullable=True),
            sa.Column('sector_id', sa.Integer(), nullable=True),
            sa.Column('ip_pool_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=True),
            sa.Column('radius_profile', sa.String(length=100), nullable=True),
            sa.Column('bandwidth_limit_down', sa.String(length=50), nullable=True),
            sa.Column('bandwidth_limit_up', sa.String(length=50), nullable=True),
            sa.Column('activation_method', sa.String(length=50), nullable=True),
            sa.Column('provisioning_script', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception as e:
        # Likely the table already exists; log and proceed so migration stays idempotent
        print(f"internet_services already exists: {e}")
    else:
        op.create_index(op.f('ix_internet_services_id'), 'internet_services', ['id'], unique=False)
        op.create_index(op.f('ix_internet_services_name'), 'internet_services', ['name'], unique=False)
    
    # Create voice_services table
    op.create_table(
        'voice_services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('included_minutes', sa.Integer(), nullable=True),
        sa.Column('per_minute_rate', sa.DECIMAL(precision=6, scale=4), nullable=False),
        sa.Column('monthly_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('setup_fee', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('cancellation_fee', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('codec', sa.String(length=50), nullable=True),
        sa.Column('quality', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('route_prefix', sa.String(length=20), nullable=True),
        sa.Column('gateway_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_voice_services_id'), 'voice_services', ['id'], unique=False)
    op.create_index(op.f('ix_voice_services_name'), 'voice_services', ['name'], unique=False)
    
    # Create bundle_services table
    op.create_table(
        'bundle_services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('internet_service_id', sa.Integer(), nullable=True),
        sa.Column('voice_service_id', sa.Integer(), nullable=True),
        sa.Column('bundle_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('individual_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('discount_amount', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('discount_percentage', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('minimum_term_months', sa.Integer(), nullable=True),
        sa.Column('early_termination_fee', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['internet_service_id'], ['internet_services.id'], ),
        sa.ForeignKeyConstraint(['voice_service_id'], ['voice_services.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bundle_services_id'), 'bundle_services', ['id'], unique=False)
    op.create_index(op.f('ix_bundle_services_name'), 'bundle_services', ['name'], unique=False)
    
    # Create recurring_services table
    op.create_table(
        'recurring_services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('service_type', sa.String(length=50), nullable=False),
        sa.Column('billing_cycle', sa.String(length=20), nullable=True),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('setup_fee', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_addon', sa.Boolean(), nullable=True),
        sa.Column('auto_provision', sa.Boolean(), nullable=True),
        sa.Column('provisioning_script', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recurring_services_id'), 'recurring_services', ['id'], unique=False)
    op.create_index(op.f('ix_recurring_services_name'), 'recurring_services', ['name'], unique=False)
    
    # Create service_tariffs table
    op.create_table(
        'service_tariffs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tariff_type', sa.String(length=50), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('base_price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('billing_cycle', sa.String(length=20), nullable=True),
        sa.Column('has_usage_limits', sa.Boolean(), nullable=True),
        sa.Column('overage_rate', sa.DECIMAL(precision=6, scale=4), nullable=True),
        sa.Column('promotional_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('promotion_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True),
        sa.Column('available_regions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_tariffs_id'), 'service_tariffs', ['id'], unique=False)
    op.create_index(op.f('ix_service_tariffs_name'), 'service_tariffs', ['name'], unique=False)


def downgrade() -> None:
    # Drop service management tables
    op.drop_index(op.f('ix_service_tariffs_name'), table_name='service_tariffs')
    op.drop_index(op.f('ix_service_tariffs_id'), table_name='service_tariffs')
    op.drop_table('service_tariffs')
    
    op.drop_index(op.f('ix_recurring_services_name'), table_name='recurring_services')
    op.drop_index(op.f('ix_recurring_services_id'), table_name='recurring_services')
    op.drop_table('recurring_services')
    
    op.drop_index(op.f('ix_bundle_services_name'), table_name='bundle_services')
    op.drop_index(op.f('ix_bundle_services_id'), table_name='bundle_services')
    op.drop_table('bundle_services')
    
    op.drop_index(op.f('ix_voice_services_name'), table_name='voice_services')
    op.drop_index(op.f('ix_voice_services_id'), table_name='voice_services')
    op.drop_table('voice_services')
    
    op.drop_index(op.f('ix_internet_services_name'), table_name='internet_services')
    op.drop_index(op.f('ix_internet_services_id'), table_name='internet_services')
    op.drop_table('internet_services')
