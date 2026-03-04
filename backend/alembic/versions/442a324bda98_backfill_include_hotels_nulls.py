"""backfill include_hotels nulls

Revision ID: 442a324bda98
Revises: 079ce4a26052
Create Date: 2026-03-04 17:27:18.139651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '442a324bda98'
down_revision: Union[str, None] = '079ce4a26052'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE trips SET include_hotels = false WHERE include_hotels IS NULL")
    op.alter_column('trips', 'include_hotels', nullable=False, server_default=sa.text('false'))


def downgrade() -> None:
    op.alter_column('trips', 'include_hotels', nullable=True, server_default=None)
