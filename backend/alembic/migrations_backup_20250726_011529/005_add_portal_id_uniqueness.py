"""Add portal ID uniqueness constraint and portal configuration table

Revision ID: 005_add_portal_id_uniqueness
Revises: 004_add_specialized_services
Create Date: 2025-07-23 19:16:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_portal_id_uniqueness'
down_revision = '7fbe30f0c3ed'
branch_labels = None
depends_on = None


def upgrade():
    # Create portal configuration table
    op.create_table(
        'portal_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('prefix', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('service_type', sa.String(length=50), nullable=False, server_default='internet'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        # Note: Removed foreign key constraint to partners table as it doesn't exist yet
    )
    
    # Create indexes for portal_config
    op.create_index('idx_portal_config_partner_id', 'portal_config', ['partner_id'])
    op.create_index('idx_portal_config_prefix', 'portal_config', ['prefix'])
    op.create_index('idx_portal_config_service_type', 'portal_config', ['service_type'])
    
    # Create unique constraint for default config per partner
    op.create_index(
        'idx_portal_config_partner_default',
        'portal_config',
        ['partner_id'],
        unique=True,
        postgresql_where=sa.text('is_default = true')
    )
    
    # Insert default portal configuration
    op.execute("""
        INSERT INTO portal_config (partner_id, prefix, description, service_type, is_default, is_active)
        VALUES (1, '1000', 'Default portal prefix for main partner', 'internet', true, true)
    """)
    
    # Create portal ID history table for auditing
    op.create_table(
        'portal_id_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('old_portal_id', sa.String(length=50), nullable=True),
        sa.Column('new_portal_id', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers_extended.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['administrators.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for portal_id_history
    op.create_index('idx_portal_id_history_customer_id', 'portal_id_history', ['customer_id'])
    op.create_index('idx_portal_id_history_changed_at', 'portal_id_history', ['changed_at'])
    
    # Add unique constraint to customers_extended.login (portal ID)
    # First, ensure no duplicate portal IDs exist
    op.execute("""
        UPDATE customers_extended 
        SET login = 'temp_' || id || '_' || EXTRACT(epoch FROM now())::bigint
        WHERE login IN (
            SELECT login 
            FROM customers_extended 
            GROUP BY login 
            HAVING COUNT(*) > 1
        )
    """)
    
    # Now add the unique constraint
    op.create_unique_constraint('uq_customers_extended_login', 'customers_extended', ['login'])
    
    # Create index for performance
    op.create_index('idx_customers_extended_portal_id', 'customers_extended', ['login'])


def downgrade():
    # Remove indexes and constraints
    op.drop_index('idx_customers_extended_portal_id', table_name='customers_extended')
    op.drop_constraint('uq_customers_extended_login', 'customers_extended', type_='unique')
    
    # Drop portal_id_history table
    op.drop_index('idx_portal_id_history_changed_at', table_name='portal_id_history')
    op.drop_index('idx_portal_id_history_customer_id', table_name='portal_id_history')
    op.drop_table('portal_id_history')
    
    # Drop portal_config table
    op.drop_index('idx_portal_config_partner_default', table_name='portal_config')
    op.drop_index('idx_portal_config_service_type', table_name='portal_config')
    op.drop_index('idx_portal_config_prefix', table_name='portal_config')
    op.drop_index('idx_portal_config_partner_id', table_name='portal_config')
    op.drop_table('portal_config')
