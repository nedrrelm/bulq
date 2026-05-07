"""Add sales, sale_products tables and sale_id to runs

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-07 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: str | Sequence[str] | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create sales and sale_products tables, add sale_id to runs."""
    # Create sales table
    op.create_table(
        'sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('state', sa.String(), nullable=False, server_default='planning'),
        sa.Column('invite_token', sa.String(), nullable=False),
        sa.Column(
            'planning_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.Column('active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('shopping_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('distributing_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id']),
        sa.UniqueConstraint('invite_token'),
    )
    op.create_index('ix_sales_seller_id', 'sales', ['seller_id'])
    op.create_index('ix_sales_state', 'sales', ['state'])
    op.create_index('ix_sales_invite_token', 'sales', ['invite_token'])
    op.create_index('ix_sales_seller_state', 'sales', ['seller_id', 'state'])

    # Create sale_products table
    op.create_table(
        'sale_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('price', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('available_quantity', sa.DECIMAL(10, 2), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['sale_id'], ['sales.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )
    op.create_index('ix_sale_products_sale_id', 'sale_products', ['sale_id'])
    op.create_index('ix_sale_products_product_id', 'sale_products', ['product_id'])
    op.create_index(
        'ix_sale_products_sale_product',
        'sale_products',
        ['sale_id', 'product_id'],
        unique=True,
    )

    # Add sale_id column to runs
    op.add_column(
        'runs',
        sa.Column('sale_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_runs_sale_id', 'runs', ['sale_id'])
    op.create_foreign_key('fk_runs_sale_id', 'runs', 'sales', ['sale_id'], ['id'])


def downgrade() -> None:
    """Drop sales tables and sale_id from runs."""
    op.drop_constraint('fk_runs_sale_id', 'runs', type_='foreignkey')
    op.drop_index('ix_runs_sale_id', table_name='runs')
    op.drop_column('runs', 'sale_id')

    op.drop_index('ix_sale_products_sale_product', table_name='sale_products')
    op.drop_index('ix_sale_products_product_id', table_name='sale_products')
    op.drop_index('ix_sale_products_sale_id', table_name='sale_products')
    op.drop_table('sale_products')

    op.drop_index('ix_sales_seller_state', table_name='sales')
    op.drop_index('ix_sales_invite_token', table_name='sales')
    op.drop_index('ix_sales_state', table_name='sales')
    op.drop_index('ix_sales_seller_id', table_name='sales')
    op.drop_table('sales')
