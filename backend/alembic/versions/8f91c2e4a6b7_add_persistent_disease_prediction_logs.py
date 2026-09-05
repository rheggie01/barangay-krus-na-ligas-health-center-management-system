"""add persistent disease prediction logs

Revision ID: 8f91c2e4a6b7
Revises: 653348390431
Create Date: 2026-09-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f91c2e4a6b7"
down_revision: Union[str, None] = "653348390431"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "disease_prediction_logs",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "consultation_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "performed_by",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "model_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "predicted_disease_code",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "predicted_disease_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "top_probability",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "probabilities",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "age",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "sex",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "symptom_codes",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "temperature",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "heart_rate",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "respiratory_rate",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "oxygen_saturation",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "development_status",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "decision_support_notice",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text(
                "CURRENT_TIMESTAMP"
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"],
            ["consultations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["performed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    for name, columns in [
        (
            "ix_disease_prediction_logs_id",
            ["id"],
        ),
        (
            "ix_disease_prediction_logs_consultation_id",
            ["consultation_id"],
        ),
        (
            "ix_disease_prediction_logs_patient_id",
            ["patient_id"],
        ),
        (
            "ix_disease_prediction_logs_performed_by",
            ["performed_by"],
        ),
        (
            "ix_disease_prediction_logs_model_name",
            ["model_name"],
        ),
        (
            "ix_disease_prediction_logs_predicted_disease_code",
            ["predicted_disease_code"],
        ),
        (
            "ix_disease_prediction_logs_created_at",
            ["created_at"],
        ),
    ]:
        op.create_index(
            name,
            "disease_prediction_logs",
            columns,
            unique=False,
        )


def downgrade() -> None:
    for name in [
        "ix_disease_prediction_logs_created_at",
        "ix_disease_prediction_logs_predicted_disease_code",
        "ix_disease_prediction_logs_model_name",
        "ix_disease_prediction_logs_performed_by",
        "ix_disease_prediction_logs_patient_id",
        "ix_disease_prediction_logs_consultation_id",
        "ix_disease_prediction_logs_id",
    ]:
        op.drop_index(
            name,
            table_name="disease_prediction_logs",
        )

    op.drop_table(
        "disease_prediction_logs"
    )
