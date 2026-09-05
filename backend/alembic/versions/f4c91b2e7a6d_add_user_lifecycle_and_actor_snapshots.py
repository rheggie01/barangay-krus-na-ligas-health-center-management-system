"""add user lifecycle and immutable audit/inventory actor snapshots

Revision ID: f4c91b2e7a6d
Revises: d8f2a61c9e40
Create Date: 2026-09-05

Hand-written migration.
Do NOT replace with Alembic autogenerate because this project has known
unrelated model/schema drift.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c91b2e7a6d"
down_revision: Union[str, None] = "d8f2a61c9e40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =====================================================
    # USERS: explicit lifecycle
    # =====================================================

    op.add_column(
        "users",
        sa.Column(
            "account_status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
    )

    op.create_index(
        "ix_users_account_status",
        "users",
        ["account_status"],
        unique=False,
    )

    op.add_column(
        "users",
        sa.Column(
            "status_changed_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "status_changed_by",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_users_status_changed_by",
        "users",
        ["status_changed_by"],
        unique=False,
    )

    op.add_column(
        "users",
        sa.Column(
            "status_changed_by_name_snapshot",
            sa.String(length=201),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "status_changed_by_role_snapshot",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE users
        SET account_status = 'ACTIVE'
        WHERE is_active = 1
        """
    )

    op.execute(
        """
        UPDATE users
        SET account_status = 'PENDING'
        WHERE is_active = 0
        """
    )

    # Existing inactive rows created by a prior deactivation action
    # are classified as INACTIVE rather than PENDING.
    op.execute(
        """
        UPDATE users u
        SET u.account_status = 'INACTIVE'
        WHERE u.is_active = 0
          AND EXISTS (
              SELECT 1
              FROM audit_logs a
              WHERE a.record_id = u.id
                AND UPPER(a.action) IN (
                    'USER_STATUS_UPDATE',
                    'USER_DEACTIVATE'
                )
                AND (
                    LOWER(a.description) LIKE '%inactive%'
                    OR LOWER(a.description) LIKE '%deactivat%'
                )
          )
        """
    )

    # =====================================================
    # AUDIT LOG IMMUTABLE ACTOR / SUBJECT SNAPSHOTS
    # =====================================================

    op.add_column(
        "audit_logs",
        sa.Column(
            "actor_username_snapshot",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "audit_logs",
        sa.Column(
            "actor_name_snapshot",
            sa.String(length=201),
            nullable=True,
        ),
    )

    op.add_column(
        "audit_logs",
        sa.Column(
            "subject_label_snapshot",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # =====================================================
    # INVENTORY TRANSACTION IMMUTABLE ACTOR SNAPSHOT
    # =====================================================

    op.add_column(
        "inventory_transactions",
        sa.Column(
            "recorded_by_name_snapshot",
            sa.String(length=201),
            nullable=True,
        ),
    )

    op.add_column(
        "inventory_transactions",
        sa.Column(
            "recorded_by_role_snapshot",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "inventory_transactions",
        "recorded_by_role_snapshot",
    )

    op.drop_column(
        "inventory_transactions",
        "recorded_by_name_snapshot",
    )

    op.drop_column(
        "audit_logs",
        "subject_label_snapshot",
    )

    op.drop_column(
        "audit_logs",
        "actor_name_snapshot",
    )

    op.drop_column(
        "audit_logs",
        "actor_username_snapshot",
    )

    op.drop_column(
        "users",
        "status_changed_by_role_snapshot",
    )

    op.drop_column(
        "users",
        "status_changed_by_name_snapshot",
    )

    op.drop_index(
        "ix_users_status_changed_by",
        table_name="users",
    )

    op.drop_column(
        "users",
        "status_changed_by",
    )

    op.drop_column(
        "users",
        "status_changed_at",
    )

    op.drop_index(
        "ix_users_account_status",
        table_name="users",
    )

    op.drop_column(
        "users",
        "account_status",
    )
