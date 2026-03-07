"""add_fk_user_id_to_trips

Revision ID: d5cf59621d9a
Revises: e797f27223ad
Create Date: 2026-03-06 21:15:19.171912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5cf59621d9a'
down_revision: Union[str, None] = 'e797f27223ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill all existing trips to your account (id=2)
    op.execute("UPDATE trips SET user_id = 2 WHERE user_id IS NULL")

    # Add FK constraint
    op.create_foreign_key(
        'fk_trips_user_id',
        'trips', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('fk_trips_user_id', 'trips', type_='foreignkey')
