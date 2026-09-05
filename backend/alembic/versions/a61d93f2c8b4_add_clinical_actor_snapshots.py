"""add clinical immutable actor snapshots

Revision ID: a61d93f2c8b4
Revises: f4c91b2e7a6d
Create Date: 2026-09-05

Hand-written migration.
Do NOT use Alembic autogenerate for this project because unrelated
model/schema drift is known to exist.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a61d93f2c8b4"
down_revision: Union[str, None] = "f4c91b2e7a6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table_name, name_field, role_field in [
        (
            "consultations",
            "recorded_by_name_snapshot",
            "recorded_by_role_snapshot",
        ),
        (
            "consultation_medicines",
            "dispensed_by_name_snapshot",
            "dispensed_by_role_snapshot",
        ),
        (
            "patient_medical_histories",
            "recorded_by_name_snapshot",
            "recorded_by_role_snapshot",
        ),
    ]:
        op.add_column(
            table_name,
            sa.Column(
                name_field,
                sa.String(length=201),
                nullable=True,
            ),
        )
        op.add_column(
            table_name,
            sa.Column(
                role_field,
                sa.String(length=255),
                nullable=True,
            ),
        )

    for column_name, length in [
        ("recorded_by_name_snapshot", 201),
        ("recorded_by_role_snapshot", 255),
        ("validated_by_name_snapshot", 201),
        ("validated_by_role_snapshot", 255),
    ]:
        op.add_column(
            "disease_cases",
            sa.Column(
                column_name,
                sa.String(length=length),
                nullable=True,
            ),
        )


def downgrade() -> None:
    for column_name in [
        "validated_by_role_snapshot",
        "validated_by_name_snapshot",
        "recorded_by_role_snapshot",
        "recorded_by_name_snapshot",
    ]:
        op.drop_column(
            "disease_cases",
            column_name,
        )

    for table_name, role_field, name_field in [
        (
            "patient_medical_histories",
            "recorded_by_role_snapshot",
            "recorded_by_name_snapshot",
        ),
        (
            "consultation_medicines",
            "dispensed_by_role_snapshot",
            "dispensed_by_name_snapshot",
        ),
        (
            "consultations",
            "recorded_by_role_snapshot",
            "recorded_by_name_snapshot",
        ),
    ]:
        op.drop_column(
            table_name,
            role_field,
        )
        op.drop_column(
            table_name,
            name_field,
        )
