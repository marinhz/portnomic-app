"""Add mail_connections table

Revision ID: 20260304_mail_conn
Revises: 20260303_perf_gdpr
Create Date: 2026-03-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20260304_mail_conn"
down_revision = "20260303_perf_gdpr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mail_connections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("display_email", sa.String(320), nullable=True),
        sa.Column("encrypted_credentials", sa.Text, nullable=True),
        sa.Column("imap_host", sa.String(255), nullable=True),
        sa.Column("imap_port", sa.Integer, nullable=True),
        sa.Column("imap_user", sa.String(320), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="connected"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_cursor", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_mail_connections_tenant_provider_email",
        "mail_connections",
        ["tenant_id", "provider", "display_email"],
        unique=True,
    )
    op.create_index(
        "ix_mail_connections_tenant_status",
        "mail_connections",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_mail_connections_tenant_status", table_name="mail_connections")
    op.drop_index("ix_mail_connections_tenant_provider_email", table_name="mail_connections")
    op.drop_table("mail_connections")
