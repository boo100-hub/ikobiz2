"""phase1_fulfillment_and_payment_fields

Revision ID: beb50c30c376
Revises: bd25c7303bc5
Create Date: 2026-05-29 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'beb50c30c376'
down_revision: Union[str, Sequence[str], None] = 'bd25c7303bc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Shop new columns
    op.add_column('shops', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('shops', sa.Column('location_area', sa.String(200), nullable=True))
    op.add_column('shops', sa.Column('location_gps_lat', sa.Float(), nullable=True))
    op.add_column('shops', sa.Column('location_gps_lng', sa.Float(), nullable=True))
    op.add_column('shops', sa.Column('fulfillment_modes', sa.String(100), nullable=True))
    op.add_column('shops', sa.Column('delivery_radius_km', sa.Float(), nullable=True, server_default='0'))
    op.add_column('shops', sa.Column('delivery_fee', sa.Float(), nullable=True, server_default='0'))
    op.add_column('shops', sa.Column('operating_hours', sa.Text(), nullable=True))
    op.add_column('shops', sa.Column('payment_methods', sa.String(200), nullable=True))
    op.add_column('shops', sa.Column('pickup_address', sa.Text(), nullable=True))
    op.add_column('shops', sa.Column('phone', sa.String(20), nullable=True))

    # Product new columns
    op.add_column('products', sa.Column('category', sa.String(100), nullable=True))
    op.add_column('products', sa.Column('attributes', sa.Text(), nullable=True))

    # Order new columns (alter OrderStatus enum to include CONFIRMED, DISPATCHED)
    op.add_column('orders', sa.Column('fulfillment_method', sa.String(20), nullable=True))
    op.add_column('orders', sa.Column('delivery_area', sa.String(200), nullable=True))
    op.add_column('orders', sa.Column('delivery_address', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('delivery_fee', sa.Float(), nullable=True, server_default='0'))
    op.add_column('orders', sa.Column('payment_method', sa.String(30), nullable=True))
    op.add_column('orders', sa.Column('payment_status', sa.String(20), nullable=True, server_default='pending'))
    op.add_column('orders', sa.Column('customer_phone', sa.String(20), nullable=True))
    op.add_column('orders', sa.Column('customer_name', sa.String(100), nullable=True))
    op.add_column('orders', sa.Column('seller_notes', sa.Text(), nullable=True))

    # Update OrderStatus enum — SQLAlchemy enums are PostgreSQL native enums
    # We need to alter the enum type to add CONFIRMED and DISPATCHED
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'CONFIRMED'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'DISPATCHED'")


def downgrade() -> None:
    # Shop
    op.drop_column('shops', 'category')
    op.drop_column('shops', 'location_area')
    op.drop_column('shops', 'location_gps_lat')
    op.drop_column('shops', 'location_gps_lng')
    op.drop_column('shops', 'fulfillment_modes')
    op.drop_column('shops', 'delivery_radius_km')
    op.drop_column('shops', 'delivery_fee')
    op.drop_column('shops', 'operating_hours')
    op.drop_column('shops', 'payment_methods')
    op.drop_column('shops', 'pickup_address')
    op.drop_column('shops', 'phone')

    # Product
    op.drop_column('products', 'category')
    op.drop_column('products', 'attributes')

    # Order
    op.drop_column('orders', 'fulfillment_method')
    op.drop_column('orders', 'delivery_area')
    op.drop_column('orders', 'delivery_address')
    op.drop_column('orders', 'delivery_fee')
    op.drop_column('orders', 'payment_method')
    op.drop_column('orders', 'payment_status')
    op.drop_column('orders', 'customer_phone')
    op.drop_column('orders', 'customer_name')
    op.drop_column('orders', 'seller_notes')

    # Note: PostgreSQL does not allow removing enum values easily.
    # CONFIRMED and DISPATCHED will remain in the enum type on downgrade.
