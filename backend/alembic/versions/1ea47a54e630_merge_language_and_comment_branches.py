"""merge language and comment branches

Revision ID: 1ea47a54e630
Revises: 95ea765a02a6, 6e0f7g1c3d4h
Create Date: 2025-11-20 23:12:33.971597

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '1ea47a54e630'
down_revision: str | Sequence[str] | None = ('95ea765a02a6', '6e0f7g1c3d4h')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
