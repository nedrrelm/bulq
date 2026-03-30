"""add_comment_to_product_bids

Revision ID: 95ea765a02a6
Revises: 5d9e6f0b2c3g
Create Date: 2025-11-12 22:03:16.796293

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '95ea765a02a6'
down_revision: str | Sequence[str] | None = '5d9e6f0b2c3g'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add comment column to product_bids table."""
    op.add_column('product_bids', sa.Column('comment', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove comment column from product_bids table."""
    op.drop_column('product_bids', 'comment')
