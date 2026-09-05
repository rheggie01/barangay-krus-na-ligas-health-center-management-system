"""add patient pwd status

Revision ID: d8f2a61c9e40
Revises: c7d4a91e2f30
Create Date: 2026-09-05

Hand-written migration.
Do not replace with Alembic autogenerate because the project contains
known schema/model drift outside this change.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8f2a61c9e40"
down_revision: Union[str, None] = "c7d4a91e2f30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column(
            "is_pwd",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "patients",
        "is_pwd",
    )
