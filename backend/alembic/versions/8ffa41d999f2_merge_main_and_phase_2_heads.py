"""merge_main_and_phase_2_heads

Revision ID: 8ffa41d999f2
Revises: 333dd530f18f, d5e3f2a1b94c
Create Date: 2026-11-01 02:08:27.400091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ffa41d999f2'
down_revision: Union[str, Sequence[str], None] = ('333dd530f18f', 'd5e3f2a1b94c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
