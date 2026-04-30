"""add character_documents

Revision ID: c3d4e5f6g7h8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-30 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('character_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('character_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=300), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False, server_default='text/plain'),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_character_documents_character_id'), 'character_documents', ['character_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_character_documents_character_id'), table_name='character_documents')
    op.drop_table('character_documents')
