"""Add anomalies table for AI Leakage Detector

Revision ID: 20260313_leakage_anomalies
Revises: 20260308_mypos
Create Date: 2026-03-13

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260313_leakage_anomalies"
down_revision = "20260308_mypos"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "anomalies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "email_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("emails.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "da_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("disbursement_accounts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "port_call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("port_calls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(20), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("line_item_ref", sa.String(512), nullable=True),
        sa.Column("invoiced_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("expected_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("raw_evidence", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_anomalies_tenant_email",
        "anomalies",
        ["tenant_id", "email_id"],
    )
    op.create_index(
        "ix_anomalies_tenant_da",
        "anomalies",
        ["tenant_id", "da_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_anomalies_tenant_da", table_name="anomalies")
    op.drop_index("ix_anomalies_tenant_email", table_name="anomalies")
    op.drop_table("anomalies")
