"""drop_secondary_market_tables

Revision ID: 3427ceb1f266
Revises: beb50c30c376
Create Date: 2026-05-31 15:23:50.922523

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3427ceb1f266'
down_revision: Union[str, Sequence[str], None] = 'beb50c30c376'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop FK constraints before dropping referenced tables (if they exist)
    conn = op.get_bind()
    # Check and drop cart_items_listing_id_fkey if it exists
    if conn.dialect.has_table(conn, 'cart_items'):
        inspector = sa.inspect(conn)
        fk_constraints = [fk['name'] for fk in inspector.get_foreign_keys('cart_items')]
        if 'cart_items_listing_id_fkey' in fk_constraints:
            op.drop_constraint('cart_items_listing_id_fkey', 'cart_items', type_='foreignkey')
    # Check and drop order_items_listing_id_fkey if it exists
    if conn.dialect.has_table(conn, 'order_items'):
        inspector = sa.inspect(conn)
        fk_constraints = [fk['name'] for fk in inspector.get_foreign_keys('order_items')]
        if 'order_items_listing_id_fkey' in fk_constraints:
            op.drop_constraint('order_items_listing_id_fkey', 'order_items', type_='foreignkey')

    # 2. Drop listing_id columns
    op.drop_column('cart_items', 'listing_id')
    op.drop_column('order_items', 'listing_id')

    # 3. Drop secondary market tables
    op.drop_index(op.f('ix_negotiations_id'), table_name='negotiations')
    op.drop_table('negotiations')
    op.drop_index(op.f('ix_ikobiz_listings_id'), table_name='ikobiz_listings')
    op.drop_table('ikobiz_listings')

    # 4. Fix messages index (auto-generated cleanup)
    op.drop_index(op.f('ix_messages_order_id'), table_name='messages')
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.create_index(op.f('ix_messages_order_id'), 'messages', ['order_id'], unique=False)

    op.create_table('ikobiz_listings',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('seller_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('seller_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('starting_price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('image_url', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('OPEN', 'NEGOTIATING', 'CLOSED', name='ikobizlistingstatus'), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('buy_now_price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('quantity', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['seller_id'], ['users.id'], name=op.f('ikobiz_listings_seller_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('ikobiz_listings_pkey'))
    )
    op.create_index(op.f('ix_ikobiz_listings_id'), 'ikobiz_listings', ['id'], unique=False)
    op.create_table('negotiations',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('ikobiz_listing_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('buyer_name', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('offer_price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('message', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('is_counter_offer', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['ikobiz_listing_id'], ['ikobiz_listings.id'], name=op.f('negotiations_ikobiz_listing_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('negotiations_pkey'))
    )
    op.create_index(op.f('ix_negotiations_id'), 'negotiations', ['id'], unique=False)

    op.add_column('order_items', sa.Column('listing_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('order_items_listing_id_fkey'), 'order_items', 'ikobiz_listings', ['listing_id'], ['id'])
    op.add_column('cart_items', sa.Column('listing_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('cart_items_listing_id_fkey'), 'cart_items', 'ikobiz_listings', ['listing_id'], ['id'])
