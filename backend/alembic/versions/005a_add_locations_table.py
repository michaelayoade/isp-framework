"""Add locations table

Revision ID: 005a_add_locations_table
Revises: 005_add_portal_id_uniqueness
Create Date: 2025-07-23 22:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005a_add_locations_table'
down_revision = '005_add_portal_id_uniqueness'
branch_labels = None
depends_on = None


def upgrade():
    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        # Extended Location Data
        sa.Column('address_line_1', sa.String(length=255), nullable=True),
        sa.Column('address_line_2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state_province', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        # Geographic Data
        sa.Column('latitude', sa.DECIMAL(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.DECIMAL(precision=11, scale=8), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        # Framework Integration
        sa.Column('custom_fields', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)

    # Insert default locations
    op.execute("""
        INSERT INTO locations (name, city, country, timezone) VALUES 
        ('Main Office', 'Lagos', 'Nigeria', 'Africa/Lagos'),
        ('Data Center', 'Abuja', 'Nigeria', 'Africa/Lagos'),
        ('Branch Office', 'Port Harcourt', 'Nigeria', 'Africa/Lagos')
        ON CONFLICT DO NOTHING;
    """)


def downgrade():
    op.drop_table('locations')
