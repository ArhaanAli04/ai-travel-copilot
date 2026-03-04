"""fix include_flights include_hotels not nullable

Revision ID: 4c1becb67984
Revises: 442a324bda98
Create Date: 2026-03-04 17:33:33.366359

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c1becb67984'
down_revision: Union[str, None] = '442a324bda98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE trips SET include_flights = false WHERE include_flights IS NULL")
    op.execute("UPDATE trips SET include_hotels = false WHERE include_hotels IS NULL")
    op.alter_column('trips', 'include_flights', nullable=False, server_default=sa.text('false'))
    op.alter_column('trips', 'include_hotels', nullable=False, server_default=sa.text('false'))


def downgrade() -> None:
    op.alter_column('trips', 'include_flights', nullable=True, server_default=None)
    op.alter_column('trips', 'include_hotels', nullable=True, server_default=None)
