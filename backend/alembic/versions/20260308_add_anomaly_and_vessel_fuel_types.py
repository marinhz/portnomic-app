"""Add anomaly_flags, status to emission_reports; allowed_fuel_types to vessels

Revision ID: 20260308_anomaly
Revises: 20260308_emission
Create Date: 2026-03-08

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260308_anomaly"
down_revision = "20260308_emission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "emission_reports",
        sa.Column("status", sa.String(20), nullable=False, server_default="verified"),
    )
    op.add_column(
        "emission_reports",
        sa.Column("anomaly_flags", postgresql.JSONB(), nullable=True),
    )

    op.add_column(
        "vessels",
        sa.Column("allowed_fuel_types", postgresql.ARRAY(sa.String()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("emission_reports", "anomaly_flags")
    op.drop_column("emission_reports", "status")
    op.drop_column("vessels", "allowed_fuel_types")
