"""add service_type_id to customer_services

Revision ID: 20250801_add_service_type_id
Revises: 459b57aef5cc
Create Date: 2025-08-01 11:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_service_type_id_001'
down_revision = '459b57aef5cc'
branch_labels = None
depends_on = None


def upgrade():
    """Add service_type_id column to customer_services table"""
    # Add service_type_id column to customer_services table
    op.add_column('customer_services', 
                  sa.Column('service_type_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint to service_types table
    op.create_foreign_key('fk_customer_services_service_type_id', 
                         'customer_services', 'service_types', 
                         ['service_type_id'], ['id'])


def downgrade():
    """Remove service_type_id column from customer_services table"""
    # Drop foreign key constraint first
    op.drop_constraint('fk_customer_services_service_type_id', 
                      'customer_services', type_='foreignkey')
    
    # Drop the column
    op.drop_column('customer_services', 'service_type_id')
