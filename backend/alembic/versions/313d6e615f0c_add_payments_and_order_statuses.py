"""add_payments_and_order_statuses

Revision ID: 313d6e615f0c
Revises: 3598bbcbd695
Create Date: 2026-06-24 16:19:23.858340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '313d6e615f0c'
down_revision: Union[str, Sequence[str], None] = '3598bbcbd695'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create payments table
    op.create_table('payments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('checkout_request_id', sa.String(length=100), nullable=True),
    sa.Column('merchant_request_id', sa.String(length=100), nullable=True),
    sa.Column('mpesa_receipt_number', sa.String(length=50), nullable=True),
    sa.Column('transaction_date', sa.String(length=20), nullable=True),
    sa.Column('result_code', sa.Integer(), nullable=True),
    sa.Column('result_desc', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)

    # Add missing values to the orderstatus ENUM type.
    # DB currently: PENDING, PAID, SHIPPED, DELIVERED, CANCELLED
    # Need to add:  CONFIRMED, DISPATCHED, SCHEDULED, IN_PROGRESS, COMPLETED
    for val in ['CONFIRMED', 'DISPATCHED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED']:
        try:
            op.execute(f"ALTER TYPE orderstatus ADD VALUE '{val}'")
        except Exception:
            pass  # Value may already exist


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')

    # Cannot remove values from a PostgreSQL ENUM; the column stays as-is.
    # A full downgrade would require recreating the table.
    pass
