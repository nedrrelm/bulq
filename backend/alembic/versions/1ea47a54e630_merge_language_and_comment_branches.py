"""merge language and comment branches

Revision ID: 1ea47a54e630
Revises: 95ea765a02a6, 6e0f7g1c3d4h
Create Date: 2025-11-20 23:12:33.971597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ea47a54e630'
down_revision: Union[str, Sequence[str], None] = ('95ea765a02a6', '6e0f7g1c3d4h')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
