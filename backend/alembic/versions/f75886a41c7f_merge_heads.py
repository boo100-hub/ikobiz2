"""merge heads

Revision ID: f75886a41c7f
Revises: 2e97df3f09b7, 3427ceb1f266
Create Date: 2026-06-03 02:04:35.481304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f75886a41c7f'
down_revision: Union[str, Sequence[str], None] = ('2e97df3f09b7', '3427ceb1f266')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
