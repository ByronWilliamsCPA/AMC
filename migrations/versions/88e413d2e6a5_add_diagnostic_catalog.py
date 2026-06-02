"""add diagnostic catalog

Revision ID: 88e413d2e6a5
Revises: d8e219f529db
Create Date: 2026-06-02 05:59:12.316893

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "88e413d2e6a5"
down_revision: str | Sequence[str] | None = "d8e219f529db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: add the diagnostic catalog reference table."""
    op.create_table(
        "diagnostic_catalog",
        sa.Column("course", sa.String(length=120), nullable=False),
        sa.Column("gate", sa.String(length=16), nullable=False),
        sa.Column("min_score", sa.Float(), nullable=True),
        sa.Column("note", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("course"),
    )


def downgrade() -> None:
    """Downgrade schema: drop the diagnostic catalog reference table."""
    op.drop_table("diagnostic_catalog")
