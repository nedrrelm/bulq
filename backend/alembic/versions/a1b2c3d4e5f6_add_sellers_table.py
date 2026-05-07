"""Add sellers table

Revision ID: a1b2c3d4e5f6
Revises: fccc4b28f193
Create Date: 2026-05-07 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = 'fccc4b28f193'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create sellers table."""
    op.create_table(
        'sellers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('invite_token', sa.String(), nullable=False),
        sa.Column(
            'is_joining_allowed', sa.Boolean(), nullable=False, server_default=sa.text('true')
        ),
        sa.Column('is_searchable', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id']),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('invite_token'),
    )
    op.create_index('ix_sellers_user_id', 'sellers', ['user_id'])
    op.create_index('ix_sellers_store_id', 'sellers', ['store_id'])
    op.create_index('ix_sellers_invite_token', 'sellers', ['invite_token'])


def downgrade() -> None:
    """Drop sellers table."""
    op.drop_index('ix_sellers_invite_token', table_name='sellers')
    op.drop_index('ix_sellers_store_id', table_name='sellers')
    op.drop_index('ix_sellers_user_id', table_name='sellers')
    op.drop_table('sellers')
