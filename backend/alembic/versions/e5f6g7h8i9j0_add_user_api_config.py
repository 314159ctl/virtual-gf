"""add api_base_url and api_model to users

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-05-15 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('api_base_url', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('api_model', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'api_model')
    op.drop_column('users', 'api_base_url')
