"""Add leader_fee column to runs

Revision ID: fccc4b28f193
Revises: 1ea47a54e630
Create Date: 2026-05-04 08:50:59.893250

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fccc4b28f193'
down_revision: str | Sequence[str] | None = '1ea47a54e630'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add leader_fee column to runs table."""
    op.add_column('runs', sa.Column('leader_fee', sa.DECIMAL(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    """Remove leader_fee column from runs table."""
    op.drop_column('runs', 'leader_fee')
