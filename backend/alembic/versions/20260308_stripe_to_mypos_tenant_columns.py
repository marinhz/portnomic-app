"""Rename Stripe columns to myPOS (Task 8.6)

Revision ID: 20260308_mypos
Revises: 20260308_llm_config
Create Date: 2026-03-08

"""

from alembic import op

revision = "20260308_mypos"
down_revision = "20260308_llm_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "tenants",
        "stripe_customer_id",
        new_column_name="mypos_customer_id",
    )
    op.alter_column(
        "tenants",
        "stripe_subscription_id",
        new_column_name="mypos_order_id",
    )


def downgrade() -> None:
    op.alter_column(
        "tenants",
        "mypos_customer_id",
        new_column_name="stripe_customer_id",
    )
    op.alter_column(
        "tenants",
        "mypos_order_id",
        new_column_name="stripe_subscription_id",
    )
