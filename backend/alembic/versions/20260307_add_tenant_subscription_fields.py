"""Add tenant subscription plan and billing fields

Revision ID: 20260307_sub
Revises: 20260304_mail_conn
Create Date: 2026-03-07

"""

import sqlalchemy as sa

from alembic import op

revision = "20260307_sub"
down_revision = "20260304_mail_conn"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("plan", sa.String(20), nullable=False, server_default="starter"),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "subscription_status",
            sa.String(20),
            nullable=False,
            server_default="trial",
        ),
    )
    op.add_column(
        "tenants",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "tenants",
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
    )

    # Backfill existing tenants: subscription_status=active (they predate billing)
    # New tenants get trial via server_default
    op.execute("UPDATE tenants SET subscription_status = 'active'")


def downgrade() -> None:
    op.drop_column("tenants", "stripe_subscription_id")
    op.drop_column("tenants", "stripe_customer_id")
    op.drop_column("tenants", "subscription_status")
    op.drop_column("tenants", "plan")
