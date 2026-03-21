"""Add discrepancies table for Sentinel Operational Gap Engine

Revision ID: 20260321_discrepancies
Revises: 20260315_port_call_agent_source
Create Date: 2026-03-21

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260321_discrepancies"
down_revision = "20260315_port_call_agent_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discrepancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "port_call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("port_calls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_documents",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("estimated_loss", sa.Numeric(18, 4), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("rule_id", sa.String(20), nullable=True),
        sa.Column("raw_evidence", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_discrepancies_tenant_port_call",
        "discrepancies",
        ["tenant_id", "port_call_id"],
    )
    op.create_index(
        "ix_discrepancies_tenant_severity",
        "discrepancies",
        ["tenant_id", "severity"],
    )


def downgrade() -> None:
    op.drop_index("ix_discrepancies_tenant_severity", table_name="discrepancies")
    op.drop_index("ix_discrepancies_tenant_port_call", table_name="discrepancies")
    op.drop_table("discrepancies")
