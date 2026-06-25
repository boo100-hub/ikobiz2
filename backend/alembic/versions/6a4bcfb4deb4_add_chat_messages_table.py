"""add_chat_messages_table

Revision ID: 6a4bcfb4deb4
Revises: bd25c7303bc5
Create Date: 2026-05-30 11:29:14.578688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6a4bcfb4deb4'
down_revision: Union[str, Sequence[str], None] = 'bd25c7303bc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_sender_created', 'chat_messages', ['sender', 'created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_sender'), 'chat_messages', ['sender'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_sender'), table_name='chat_messages')
    op.drop_index('idx_chat_sender_created', table_name='chat_messages')
    op.drop_table('chat_messages')
