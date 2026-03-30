"""Add dark_mode to users

Revision ID: 5d9e6f0b2c3g
Revises: 4c8d5e9a1b2f
Create Date: 2025-11-12 21:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5d9e6f0b2c3g'
down_revision: str | Sequence[str] | None = '4c8d5e9a1b2f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add dark_mode column to users table."""
    op.add_column(
        'users', sa.Column('dark_mode', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove dark_mode column from users table."""
    op.drop_column('users', 'dark_mode')
