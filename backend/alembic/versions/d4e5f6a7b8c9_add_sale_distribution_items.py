"""Add sale_distribution_items table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-07 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: str | Sequence[str] | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create sale_distribution_items table."""
    op.create_table(
        'sale_distribution_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('is_handed_over', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('handed_over_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )
    op.create_index('ix_sale_dist_items_sale_id', 'sale_distribution_items', ['sale_id'])
    op.create_index('ix_sale_dist_items_run_id', 'sale_distribution_items', ['run_id'])
    op.create_index('ix_sale_dist_items_product_id', 'sale_distribution_items', ['product_id'])
    op.create_index(
        'ix_sale_dist_items_sale_run_product',
        'sale_distribution_items',
        ['sale_id', 'run_id', 'product_id'],
        unique=True,
    )


def downgrade() -> None:
    """Drop sale_distribution_items table."""
    op.drop_index('ix_sale_dist_items_sale_run_product', table_name='sale_distribution_items')
    op.drop_index('ix_sale_dist_items_product_id', table_name='sale_distribution_items')
    op.drop_index('ix_sale_dist_items_run_id', table_name='sale_distribution_items')
    op.drop_index('ix_sale_dist_items_sale_id', table_name='sale_distribution_items')
    op.drop_table('sale_distribution_items')
