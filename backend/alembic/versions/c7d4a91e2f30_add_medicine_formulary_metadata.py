"""add medicine formulary and safety metadata

Revision ID: c7d4a91e2f30
Revises: 8f91c2e4a6b7
Create Date: 2026-09-05

This is a hand-written migration.
Do not replace it with Alembic autogenerate output.
"""

from alembic import op
import sqlalchemy as sa


revision = "c7d4a91e2f30"
down_revision = "8f91c2e4a6b7"
branch_labels = None
depends_on = None


def upgrade():
    # Existing medicine rows are treated as already operational
    # to preserve the current system behavior after migration.
    op.add_column(
        "medicines",
        sa.Column(
            "medicine_category",
            sa.String(length=60),
            nullable=False,
            server_default="GENERAL",
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "formulary_status",
            sa.String(length=30),
            nullable=False,
            server_default="VERIFIED",
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "program_type",
            sa.String(length=60),
            nullable=True,
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "requires_prescription",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "restricted_dispensing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "sensitive_inventory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "forecast_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )

    op.add_column(
        "medicines",
        sa.Column(
            "stock_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
    )

    op.create_index(
        "ix_medicines_medicine_category",
        "medicines",
        ["medicine_category"],
        unique=False,
    )

    op.create_index(
        "ix_medicines_formulary_status",
        "medicines",
        ["formulary_status"],
        unique=False,
    )

    op.create_index(
        "ix_medicines_program_type",
        "medicines",
        ["program_type"],
        unique=False,
    )

    op.create_index(
        "ix_medicines_sensitive_inventory",
        "medicines",
        ["sensitive_inventory"],
        unique=False,
    )

    op.create_index(
        "ix_medicines_forecast_enabled",
        "medicines",
        ["forecast_enabled"],
        unique=False,
    )

    op.create_index(
        "ix_medicines_stock_verified",
        "medicines",
        ["stock_verified"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_medicines_stock_verified",
        table_name="medicines",
    )

    op.drop_index(
        "ix_medicines_forecast_enabled",
        table_name="medicines",
    )

    op.drop_index(
        "ix_medicines_sensitive_inventory",
        table_name="medicines",
    )

    op.drop_index(
        "ix_medicines_program_type",
        table_name="medicines",
    )

    op.drop_index(
        "ix_medicines_formulary_status",
        table_name="medicines",
    )

    op.drop_index(
        "ix_medicines_medicine_category",
        table_name="medicines",
    )

    op.drop_column(
        "medicines",
        "stock_verified",
    )

    op.drop_column(
        "medicines",
        "forecast_enabled",
    )

    op.drop_column(
        "medicines",
        "sensitive_inventory",
    )

    op.drop_column(
        "medicines",
        "restricted_dispensing",
    )

    op.drop_column(
        "medicines",
        "requires_prescription",
    )

    op.drop_column(
        "medicines",
        "program_type",
    )

    op.drop_column(
        "medicines",
        "formulary_status",
    )

    op.drop_column(
        "medicines",
        "medicine_category",
    )
