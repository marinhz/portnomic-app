"""add tariffs and disbursement_accounts

Revision ID: c2d356803e41
Revises: b1c245792d30
Create Date: 2026-03-03 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c2d356803e41"
down_revision: Union[str, None] = "b1c245792d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tariffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "port_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "formula_config",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column("valid_from", sa.Date, nullable=False),
        sa.Column("valid_to", sa.Date, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_tariffs_tenant_port", "tariffs", ["tenant_id", "port_id"]
    )
    op.create_index(
        "ix_tariffs_tenant_valid", "tariffs", ["tenant_id", "valid_from", "valid_to"]
    )

    op.create_table(
        "disbursement_accounts",
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
            "tariff_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tariffs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column(
            "status", sa.String(30), nullable=False, server_default="draft"
        ),
        sa.Column(
            "line_items",
            postgresql.JSONB,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "totals",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column("currency", sa.String(3), nullable=False, server_default="'USD'"),
        sa.Column("pdf_blob_id", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_da_tenant_port_call",
        "disbursement_accounts",
        ["tenant_id", "port_call_id"],
    )
    op.create_index(
        "ix_da_tenant_status",
        "disbursement_accounts",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_da_tenant_created",
        "disbursement_accounts",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_da_tenant_created", table_name="disbursement_accounts")
    op.drop_index("ix_da_tenant_status", table_name="disbursement_accounts")
    op.drop_index("ix_da_tenant_port_call", table_name="disbursement_accounts")
    op.drop_table("disbursement_accounts")

    op.drop_index("ix_tariffs_tenant_valid", table_name="tariffs")
    op.drop_index("ix_tariffs_tenant_port", table_name="tariffs")
    op.drop_table("tariffs")
