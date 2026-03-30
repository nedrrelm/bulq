"""Add comment field to runs table

Revision ID: 44a3f2e79d67
Revises: 2f9fd584c644
Create Date: 2025-11-11 22:20:27.147289

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '44a3f2e79d67'
down_revision: str | Sequence[str] | None = '2f9fd584c644'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('runs', sa.Column('comment', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('runs', 'comment')
