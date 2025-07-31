"""Add portal ID uniqueness constraint and portal configuration table

Revision ID: 005_add_portal_id_uniqueness
Revises: 7fbe30f0c3ed
Create Date: 2025-07-23 19:16:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "005_add_portal_id_uniqueness"
down_revision = "7fbe30f0c3ed"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# UPGRADE
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """Create portal-ID related structures in an idempotent way."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # If the core table is already present we assume this migration (or a later
    # consolidated one) has already run successfully.  Exit early so the chain
    # remains idempotent.
    if inspector.has_table("portal_config"):
        return

    # ------------------------------------------------------------------
    # portal_config table + indexes + default row
    # ------------------------------------------------------------------
    op.create_table(
        "portal_config",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("prefix", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "service_type", sa.String(length=50), nullable=False, server_default="internet"
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True
        ),
    )
    op.create_index("idx_portal_config_partner_id", "portal_config", ["partner_id"])
    op.create_index("idx_portal_config_prefix", "portal_config", ["prefix"])
    op.create_index("idx_portal_config_service_type", "portal_config", ["service_type"])
    op.create_index(
        "idx_portal_config_partner_default",
        "portal_config",
        ["partner_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )

    # Insert a default portal config row for the main partner (id=1).  In the
    # unlikely event the partners table is empty, ignore the error.
    op.execute(
        """
        INSERT INTO portal_config (partner_id, prefix, description, service_type, is_default, is_active)
        VALUES (1,'1000','Default portal prefix for main partner','internet',true,true)
        ON CONFLICT DO NOTHING
        """
    )

    # ------------------------------------------------------------------
    # portal_id_history table + indexes - TEMPORARILY DISABLED
    # TODO: Re-enable after customers_extended table is created in proper order
    # ------------------------------------------------------------------
    # op.create_table(
    #     "portal_id_history",
    #     sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
    #     sa.Column("customer_id", sa.Integer(), nullable=False),
    #     sa.Column("old_portal_id", sa.String(length=50), nullable=True),
    #     sa.Column("new_portal_id", sa.String(length=50), nullable=False),
    #     sa.Column("changed_by", sa.Integer(), nullable=True),
    #     sa.Column("change_reason", sa.Text(), nullable=True),
    #     sa.Column(
    #         "changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    #     ),
    #     sa.ForeignKeyConstraint(["changed_by"], ["administrators.id"], ondelete="SET NULL"),
    # )
    # op.create_index("idx_portal_id_history_customer_id", "portal_id_history", ["customer_id"])
    # op.create_index("idx_portal_id_history_changed_at", "portal_id_history", ["changed_at"])
    pass  # Placeholder to keep migration valid

    # ------------------------------------------------------------------
    # Ensure uniqueness of customers_extended.login (portal-ID)
    # ------------------------------------------------------------------
    unique_names = {
        uc["name"] for uc in inspector.get_unique_constraints("customers_extended")
    }
    if "uq_customers_extended_login" not in unique_names:
        # Resolve any duplicates before adding the constraint.
        op.execute(
            """
            UPDATE customers_extended
            SET login = 'temp_' || id || '_' || EXTRACT(epoch FROM now())::bigint
            WHERE login IN (
                SELECT login FROM customers_extended GROUP BY login HAVING COUNT(*) > 1
            )
            """
        )
        op.create_unique_constraint(
            "uq_customers_extended_login", "customers_extended", ["login"]
        )
        op.create_index("idx_customers_extended_portal_id", "customers_extended", ["login"])


# ---------------------------------------------------------------------------
# DOWNGRADE
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """Drop portal-ID related structures (safe even if partially present)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Remove customer login index + uniqueness if they exist
    idx_names = {ix["name"] for ix in inspector.get_indexes("customers_extended")}
    if "idx_customers_extended_portal_id" in idx_names:
        op.drop_index("idx_customers_extended_portal_id", table_name="customers_extended")
    uniq_names = {uc["name"] for uc in inspector.get_unique_constraints("customers_extended")}
    if "uq_customers_extended_login" in uniq_names:
        op.drop_constraint("uq_customers_extended_login", "customers_extended", type_="unique")

    # Drop history table (and its indexes)
    if inspector.has_table("portal_id_history"):
        op.drop_index("idx_portal_id_history_changed_at", table_name="portal_id_history")
        op.drop_index("idx_portal_id_history_customer_id", table_name="portal_id_history")
        op.drop_table("portal_id_history")

    # Drop core portal_config table (and its indexes)
    if inspector.has_table("portal_config"):
        op.drop_index("idx_portal_config_partner_default", table_name="portal_config")
        op.drop_index("idx_portal_config_service_type", table_name="portal_config")
        op.drop_index("idx_portal_config_prefix", table_name="portal_config")
        op.drop_index("idx_portal_config_partner_id", table_name="portal_config")
        op.drop_table("portal_config")
