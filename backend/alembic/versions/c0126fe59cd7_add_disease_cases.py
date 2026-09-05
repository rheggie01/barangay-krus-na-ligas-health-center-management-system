"""add disease cases

Revision ID: c0126fe59cd7
Revises: ff57feaeae8c
Create Date: 2026-08-16 05:53:05.315062
"""

from typing import (
    Sequence,
    Union,
)

from alembic import op
import sqlalchemy as sa


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "c0126fe59cd7"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "ff57feaeae8c"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


# =========================================================
# UPGRADE
# =========================================================

def upgrade() -> None:
    # -----------------------------------------------------
    # DISEASE CASES
    # -----------------------------------------------------

    op.create_table(
        "disease_cases",

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "patient_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "consultation_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "disease_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "case_status",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "onset_date",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
    "case_date",
    sa.Date(),
    nullable=False,
        ),

        sa.Column(
            "remarks",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "validation_status",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "validated_by",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "validated_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "recorded_by",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text(
                "now()"
            ),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text(
                "now()"
            ),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["disease_id"],
            ["diseases.id"],
        ),

        sa.ForeignKeyConstraint(
            ["recorded_by"],
            ["users.id"],
        ),

        sa.ForeignKeyConstraint(
            ["validated_by"],
            ["users.id"],
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.UniqueConstraint(
            "consultation_id",
            "disease_id",
            name=(
                "uq_disease_case_"
                "consultation_disease"
            ),
        ),
    )


    # -----------------------------------------------------
    # DISEASE CASE INDEXES
    # -----------------------------------------------------

    op.create_index(
        "ix_disease_cases_id",
        "disease_cases",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_patient_id",
        "disease_cases",
        ["patient_id"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_consultation_id",
        "disease_cases",
        ["consultation_id"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_disease_id",
        "disease_cases",
        ["disease_id"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_case_status",
        "disease_cases",
        ["case_status"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_onset_date",
        "disease_cases",
        ["onset_date"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_case_date",
        "disease_cases",
        ["case_date"],
        unique=False,
    )

    op.create_index(
        "ix_disease_cases_validation_status",
        "disease_cases",
        ["validation_status"],
        unique=False,
    )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade() -> None:
    # -----------------------------------------------------
    # DROP INDEXES
    # -----------------------------------------------------

    op.drop_index(
        "ix_disease_cases_validation_status",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_case_date",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_onset_date",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_case_status",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_disease_id",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_consultation_id",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_patient_id",
        table_name="disease_cases",
    )

    op.drop_index(
        "ix_disease_cases_id",
        table_name="disease_cases",
    )


    # -----------------------------------------------------
    # DROP TABLE
    # -----------------------------------------------------

    op.drop_table(
        "disease_cases"
    )