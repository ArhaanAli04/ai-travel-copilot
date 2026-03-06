"""add clerk_id to users

Revision ID: e797f27223ad
Revises: 4c1becb67984
Create Date: 2026-03-06 16:02:55.836747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e797f27223ad'
down_revision: Union[str, None] = '4c1becb67984'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('clerk_id', sa.String(), nullable=True))
    op.create_unique_constraint('uq_users_clerk_id', 'users', ['clerk_id'])
    op.create_index('ix_users_clerk_id', 'users', ['clerk_id'])


def downgrade() -> None:
    op.drop_index('ix_users_clerk_id', table_name='users')
    op.drop_constraint('uq_users_clerk_id', 'users', type_='unique')
    op.drop_column('users', 'clerk_id')
