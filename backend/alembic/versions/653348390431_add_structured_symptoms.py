"""add structured symptoms

Revision ID: 653348390431
Revises: d3a8b9f4c102
Create Date: 2026-09-04 21:41:17.308236
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "653348390431"
down_revision: Union[str, Sequence[str], None] = "d3a8b9f4c102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # SYMPTOM MASTER TABLE
    # =====================================================

    op.create_table(
        "symptoms",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "code",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_symptoms_code"),
        "symptoms",
        ["code"],
        unique=True,
    )

    op.create_index(
        op.f("ix_symptoms_id"),
        "symptoms",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_symptoms_is_active"),
        "symptoms",
        ["is_active"],
        unique=False,
    )

    op.create_index(
        op.f("ix_symptoms_name"),
        "symptoms",
        ["name"],
        unique=True,
    )

    # =====================================================
    # CONSULTATION <-> SYMPTOM ASSOCIATION TABLE
    # =====================================================

    op.create_table(
        "consultation_symptoms",
        sa.Column(
            "consultation_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "symptom_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["symptom_id"],
            ["symptoms.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "consultation_id",
            "symptom_id",
        ),
    )


def downgrade() -> None:
    # Drop association table first because it references symptoms.
    op.drop_table(
        "consultation_symptoms"
    )

    op.drop_index(
        op.f("ix_symptoms_name"),
        table_name="symptoms",
    )

    op.drop_index(
        op.f("ix_symptoms_is_active"),
        table_name="symptoms",
    )

    op.drop_index(
        op.f("ix_symptoms_id"),
        table_name="symptoms",
    )

    op.drop_index(
        op.f("ix_symptoms_code"),
        table_name="symptoms",
    )

    op.drop_table(
        "symptoms"
    )
