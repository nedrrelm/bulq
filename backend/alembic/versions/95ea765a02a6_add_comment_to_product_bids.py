"""add_comment_to_product_bids

Revision ID: 95ea765a02a6
Revises: 5d9e6f0b2c3g
Create Date: 2025-11-12 22:03:16.796293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95ea765a02a6'
down_revision: Union[str, Sequence[str], None] = '5d9e6f0b2c3g'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add comment column to product_bids table."""
    op.add_column('product_bids', sa.Column('comment', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove comment column from product_bids table."""
    op.drop_column('product_bids', 'comment')
