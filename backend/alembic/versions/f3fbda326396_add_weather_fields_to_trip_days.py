"""add_weather_fields_to_trip_days

Revision ID: f3fbda326396
Revises: 07c06540ff20
Create Date: 2026-01-09 20:01:29.978045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3fbda326396'
down_revision: Union[str, None] = '07c06540ff20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add weather columns to trip_days table
    op.add_column('trip_days', sa.Column('weather_temp_high', sa.Float(), nullable=True))
    op.add_column('trip_days', sa.Column('weather_temp_low', sa.Float(), nullable=True))
    op.add_column('trip_days', sa.Column('weather_condition', sa.String(), nullable=True))
    op.add_column('trip_days', sa.Column('weather_icon', sa.String(), nullable=True))
    op.add_column('trip_days', sa.Column('weather_precipitation_prob', sa.Float(), nullable=True))

def downgrade() -> None:
    # Remove weather columns if rolling back
    op.drop_column('trip_days', 'weather_precipitation_prob')
    op.drop_column('trip_days', 'weather_icon')
    op.drop_column('trip_days', 'weather_condition')
    op.drop_column('trip_days', 'weather_temp_low')
    op.drop_column('trip_days', 'weather_temp_high')
