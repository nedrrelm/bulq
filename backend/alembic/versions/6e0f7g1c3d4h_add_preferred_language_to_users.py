"""Add preferred_language to users

Revision ID: 6e0f7g1c3d4h
Revises: 5d9e6f0b2c3g
Create Date: 2025-11-14 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6e0f7g1c3d4h'
down_revision: str | Sequence[str] | None = '5d9e6f0b2c3g'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add preferred_language column to users table."""
    op.add_column(
        'users', sa.Column('preferred_language', sa.String(5), nullable=False, server_default='en')
    )


def downgrade() -> None:
    """Remove preferred_language column from users table."""
    op.drop_column('users', 'preferred_language')
