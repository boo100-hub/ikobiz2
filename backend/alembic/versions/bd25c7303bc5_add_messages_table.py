"""add_messages_table

Revision ID: bd25c7303bc5
Revises: 36b75aac7862
Create Date: 2026-05-27 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bd25c7303bc5'
down_revision: Union[str, Sequence[str], None] = '36b75aac7862'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_auto_reply', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_messages_order_id', 'messages', ['order_id'])


def downgrade() -> None:
    op.drop_index('ix_messages_order_id', table_name='messages')
    op.drop_table('messages')
