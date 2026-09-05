"""add street to patients

Revision ID: ff57feaeae8c
Revises: a2bf8c3d1504
Create Date: 2026-08-14 02:08:08.506250

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "ff57feaeae8c"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "a2bf8c3d1504"

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
    """Add street column to patients table."""

    op.add_column(
        "patients",
        sa.Column(
            "street",
            sa.String(length=150),
            nullable=True,
        ),
    )


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade() -> None:
    """Remove street column from patients table."""

    op.drop_column(
        "patients",
        "street",
    )