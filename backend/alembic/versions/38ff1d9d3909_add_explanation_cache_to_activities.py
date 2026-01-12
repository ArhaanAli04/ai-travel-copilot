"""add_explanation_cache_to_activities

Revision ID: 38ff1d9d3909
Revises: f3fbda326396
Create Date: 2026-01-12 16:15:34.979762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38ff1d9d3909'
down_revision: Union[str, None] = 'f3fbda326396'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add explanation_cache column
    op.add_column('activities', sa.Column('explanation_cache', sa.Text(), nullable=True))
    
    # Add explanation_generated_at column
    op.add_column('activities', sa.Column('explanation_generated_at', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns if rolling back
    op.drop_column('activities', 'explanation_generated_at')
    op.drop_column('activities', 'explanation_cache')
