"""Add latitude and longitude to ports table

Revision ID: 20260315_port_coords
Revises: 20260313_demo_enterprise
Create Date: 2026-03-15

"""

import sqlalchemy as sa

from alembic import op

revision = "20260315_port_coords"
down_revision = "20260313_demo_enterprise"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ports", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("ports", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("ports", "longitude")
    op.drop_column("ports", "latitude")
