"""Create contact types lookup table

Revision ID: 20250730_create_contact_types
Revises: 20250729_merge_multiple_heads
Create Date: 2025-07-30 07:32:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250730_create_contact_types'
down_revision = '20250729_merge_multiple_heads'
branch_labels = None
depends_on = None


def upgrade():
    # Create contact_types table
    op.create_table('contact_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contact_types_id'), 'contact_types', ['id'], unique=False)
    op.create_index(op.f('ix_contact_types_code'), 'contact_types', ['code'], unique=True)
    
    # Insert default contact types
    contact_types_table = sa.table('contact_types',
        sa.column('code', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('is_active', sa.Boolean),
        sa.column('is_system', sa.Boolean),
        sa.column('sort_order', sa.Integer)
    )
    
    op.bulk_insert(contact_types_table, [
        {
            'code': 'primary',
            'name': 'Primary Contact',
            'description': 'Main point of contact for the customer',
            'is_active': True,
            'is_system': True,
            'sort_order': 1
        },
        {
            'code': 'billing',
            'name': 'Billing Contact',
            'description': 'Contact for billing and payment matters',
            'is_active': True,
            'is_system': True,
            'sort_order': 2
        },
        {
            'code': 'technical',
            'name': 'Technical Contact',
            'description': 'Contact for technical support and issues',
            'is_active': True,
            'is_system': True,
            'sort_order': 3
        },
        {
            'code': 'emergency',
            'name': 'Emergency Contact',
            'description': 'Emergency contact person',
            'is_active': True,
            'is_system': True,
            'sort_order': 4
        },
        {
            'code': 'installation',
            'name': 'Installation Contact',
            'description': 'Contact for installation and field work',
            'is_active': True,
            'is_system': False,
            'sort_order': 5
        }
    ])
    
    # Add contact_type_id column to customer_contacts table
    op.add_column('customer_contacts', sa.Column('contact_type_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'customer_contacts', 'contact_types', ['contact_type_id'], ['id'])
    
    # Migrate existing contact_type string values to contact_type_id
    # First, update existing records to use primary contact type (id=1) as default
    op.execute("UPDATE customer_contacts SET contact_type_id = 1 WHERE contact_type_id IS NULL")
    
    # Try to map existing string values to new IDs
    op.execute("""
        UPDATE customer_contacts 
        SET contact_type_id = (
            SELECT id FROM contact_types 
            WHERE contact_types.code = customer_contacts.contact_type
        )
        WHERE contact_type IN ('primary', 'billing', 'technical', 'emergency')
    """)
    
    # Make contact_type_id NOT NULL after migration
    op.alter_column('customer_contacts', 'contact_type_id', nullable=False)
    
    # Drop the old contact_type string column
    op.drop_column('customer_contacts', 'contact_type')


def downgrade():
    # Add back the contact_type string column
    op.add_column('customer_contacts', sa.Column('contact_type', sa.String(length=50), nullable=True))
    
    # Migrate contact_type_id back to string values
    op.execute("""
        UPDATE customer_contacts 
        SET contact_type = (
            SELECT code FROM contact_types 
            WHERE contact_types.id = customer_contacts.contact_type_id
        )
    """)
    
    # Set default for any NULL values
    op.execute("UPDATE customer_contacts SET contact_type = 'primary' WHERE contact_type IS NULL")
    
    # Make contact_type NOT NULL and drop foreign key
    op.alter_column('customer_contacts', 'contact_type', nullable=False)
    op.drop_constraint(None, 'customer_contacts', type_='foreignkey')
    op.drop_column('customer_contacts', 'contact_type_id')
    
    # Drop contact_types table
    op.drop_index(op.f('ix_contact_types_code'), table_name='contact_types')
    op.drop_index(op.f('ix_contact_types_id'), table_name='contact_types')
    op.drop_table('contact_types')
