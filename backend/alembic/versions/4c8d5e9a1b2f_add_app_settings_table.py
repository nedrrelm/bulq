"""Add app_settings table

Revision ID: 4c8d5e9a1b2f
Revises: 3bb59d018e5c
Create Date: 2025-11-12 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c8d5e9a1b2f'
down_revision: Union[str, Sequence[str], None] = '3bb59d018e5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create app_settings table and initialize default values."""
    # Create app_settings table
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('key')
    )

    # Insert default setting: registration enabled by default
    op.execute(
        "INSERT INTO app_settings (key, value) VALUES ('allow_registration', 'true')"
    )


def downgrade() -> None:
    """Drop app_settings table."""
    op.drop_table('app_settings')
