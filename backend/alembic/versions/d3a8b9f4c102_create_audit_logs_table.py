"""create audit logs table

Revision ID: d3a8b9f4c102
Revises: c0126fe59cd7
Create Date: 2026-08-21 18:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3a8b9f4c102"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "c0126fe59cd7"
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


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "role_names",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "action",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "module",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "record_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "ip_address",
            sa.String(length=45),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_audit_logs_id",
        "audit_logs",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_user_id",
        "audit_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_action",
        "audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_module",
        "audit_logs",
        ["module"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_record_id",
        "audit_logs",
        ["record_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_logs_created_at",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_record_id",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_module",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_action",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_user_id",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_id",
        table_name="audit_logs",
    )
    op.drop_table("audit_logs")
