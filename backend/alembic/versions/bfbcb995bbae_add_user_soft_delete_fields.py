"""add user soft delete fields

Revision ID: bfbcb995bbae
Revises: a61d93f2c8b4
Create Date: 2026-09-06 23:37:20.810446
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bfbcb995bbae"
down_revision: Union[str, Sequence[str], None] = "a61d93f2c8b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft-delete fields to users table."""

    op.add_column(
        "users",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "deleted_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "deleted_by",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_users_is_deleted",
        "users",
        ["is_deleted"],
        unique=False,
    )

    op.create_index(
        "ix_users_deleted_by",
        "users",
        ["deleted_by"],
        unique=False,
    )


def downgrade() -> None:
    """Remove soft-delete fields from users table."""

    op.drop_index(
        "ix_users_deleted_by",
        table_name="users",
    )

    op.drop_index(
        "ix_users_is_deleted",
        table_name="users",
    )

    op.drop_column(
        "users",
        "deleted_by",
    )

    op.drop_column(
        "users",
        "deleted_at",
    )

    op.drop_column(
        "users",
        "is_deleted",
    )