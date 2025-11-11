"""Convert quantity fields from integer to decimal

Revision ID: 3bb59d018e5c
Revises: 44a3f2e79d67
Create Date: 2025-11-11 22:24:35.386826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bb59d018e5c'
down_revision: Union[str, Sequence[str], None] = '44a3f2e79d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Convert quantity fields from integer to decimal(10,2) to support fractional quantities
    op.alter_column('product_bids', 'quantity',
                    existing_type=sa.Integer(),
                    type_=sa.DECIMAL(precision=10, scale=2),
                    existing_nullable=False)
    op.alter_column('product_bids', 'distributed_quantity',
                    existing_type=sa.Integer(),
                    type_=sa.DECIMAL(precision=10, scale=2),
                    existing_nullable=True)
    op.alter_column('shopping_list_items', 'requested_quantity',
                    existing_type=sa.Integer(),
                    type_=sa.DECIMAL(precision=10, scale=2),
                    existing_nullable=False)
    op.alter_column('shopping_list_items', 'purchased_quantity',
                    existing_type=sa.Integer(),
                    type_=sa.DECIMAL(precision=10, scale=2),
                    existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Convert back to integer (will truncate decimal values)
    op.alter_column('shopping_list_items', 'purchased_quantity',
                    existing_type=sa.DECIMAL(precision=10, scale=2),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('shopping_list_items', 'requested_quantity',
                    existing_type=sa.DECIMAL(precision=10, scale=2),
                    type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('product_bids', 'distributed_quantity',
                    existing_type=sa.DECIMAL(precision=10, scale=2),
                    type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('product_bids', 'quantity',
                    existing_type=sa.DECIMAL(precision=10, scale=2),
                    type_=sa.Integer(),
                    existing_nullable=False)
