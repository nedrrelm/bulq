"""Add seller_followers table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-07 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: str | Sequence[str] | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create seller_followers table."""
    op.create_table(
        'seller_followers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['seller_id'], ['sellers.id']),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id']),
    )
    op.create_index('ix_seller_followers_seller_id', 'seller_followers', ['seller_id'])
    op.create_index('ix_seller_followers_group_id', 'seller_followers', ['group_id'])
    op.create_index(
        'ix_seller_followers_seller_group',
        'seller_followers',
        ['seller_id', 'group_id'],
        unique=True,
    )


def downgrade() -> None:
    """Drop seller_followers table."""
    op.drop_index('ix_seller_followers_seller_group', table_name='seller_followers')
    op.drop_index('ix_seller_followers_group_id', table_name='seller_followers')
    op.drop_index('ix_seller_followers_seller_id', table_name='seller_followers')
    op.drop_table('seller_followers')
