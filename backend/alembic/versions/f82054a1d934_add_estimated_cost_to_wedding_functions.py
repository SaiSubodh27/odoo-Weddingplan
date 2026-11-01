"""add_estimated_cost_to_wedding_functions

Revision ID: f82054a1d934
Revises: e7193b48f912
Create Date: 2026-10-31 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select
import random
from decimal import Decimal


# revision identifiers, used by Alembic.
revision: str = 'f82054a1d934'
down_revision: Union[str, Sequence[str], None] = 'e7193b48f912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _calc_cost(name: str) -> Decimal:
    fn = (name or "").lower()
    if "mehendi" in fn or "mehndi" in fn:
        low, high = 45000, 90000
    elif "haldi" in fn:
        low, high = 40000, 85000
    elif "sangeet" in fn or "cocktail" in fn:
        low, high = 120000, 250000
    elif "wedding" in fn or "muhurtham" in fn or "phera" in fn or "varmala" in fn:
        low, high = 250000, 500000
    elif "reception" in fn:
        low, high = 175000, 350000
    else:
        low, high = 50000, 200000
    raw = random.randint(low, high)
    rounded = max(low, min(high, round(raw / 5000) * 5000))
    return Decimal(str(rounded))


def upgrade() -> None:
    # 1. Add estimated_cost column
    op.add_column(
        'wedding_functions',
        sa.Column('estimated_cost', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False)
    )

    # 2. Backfill existing rows
    conn = op.get_bind()
    wedding_functions = table(
        'wedding_functions',
        column('id', sa.String),
        column('function_name', sa.String),
        column('estimated_cost', sa.Numeric)
    )
    results = conn.execute(select(wedding_functions.c.id, wedding_functions.c.function_name)).fetchall()
    for row in results:
        cost = _calc_cost(row.function_name)
        conn.execute(
            wedding_functions.update()
            .where(wedding_functions.c.id == row.id)
            .values(estimated_cost=cost)
        )


def downgrade() -> None:
    op.drop_column('wedding_functions', 'estimated_cost')
