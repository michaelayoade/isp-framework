"""Fix RADIUS foreign key references to customer_services

Revision ID: fix_radius_foreign_keys
Revises: create_plugin_system_tables
Create Date: 2025-07-26 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'fix_radius_foreign_keys'
down_revision: Union[str, None] = 'create_plugin_system_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix foreign key references in RADIUS tables to point to customer_services instead of internet_services"""
    
    # Fix radius_sessions.service_id foreign key
    try:
        op.drop_constraint('radius_sessions_service_id_fkey', 'radius_sessions', type_='foreignkey')
    except Exception:
        pass  # Constraint might not exist
    
    try:
        op.create_foreign_key(
            'radius_sessions_service_id_fkey',
            'radius_sessions', 'customer_services',
            ['service_id'], ['id']
        )
    except Exception:
        pass  # Foreign key might already be correct
    
    # Fix customers_online.service_id foreign key
    try:
        op.drop_constraint('customers_online_service_id_fkey', 'customers_online', type_='foreignkey')
    except Exception:
        pass  # Constraint might not exist
    
    try:
        op.create_foreign_key(
            'customers_online_service_id_fkey',
            'customers_online', 'customer_services',
            ['service_id'], ['id']
        )
    except Exception:
        pass  # Foreign key might already be correct


def downgrade() -> None:
    """Revert foreign key references back to internet_services"""
    
    # Revert radius_sessions.service_id foreign key
    try:
        op.drop_constraint('radius_sessions_service_id_fkey', 'radius_sessions', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.create_foreign_key(
            'radius_sessions_service_id_fkey',
            'radius_sessions', 'internet_services',
            ['service_id'], ['id']
        )
    except Exception:
        pass
    
    # Revert customers_online.service_id foreign key
    try:
        op.drop_constraint('customers_online_service_id_fkey', 'customers_online', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.create_foreign_key(
            'customers_online_service_id_fkey',
            'customers_online', 'internet_services',
            ['service_id'], ['id']
        )
    except Exception:
        pass
