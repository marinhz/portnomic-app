"""Add documents table and extend parse_jobs for document-based parsing

Revision ID: 20260321_documents
Revises: 20260321_discrepancies
Create Date: 2026-03-21

Decouples manual uploads from Email pipeline. Manual uploads create Document rows
only; ParseJob supports document_id for document-based jobs.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260321_documents"
down_revision = "20260321_discrepancies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
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
        sa.Column("source_type", sa.String(50), nullable=False, server_default="manual_upload"),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("processing_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("ai_raw_output", postgresql.JSONB(), nullable=True),
        sa.Column("error_reason", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("audit_status", sa.String(30), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documents_tenant_port_call", "documents", ["tenant_id", "port_call_id"])
    op.create_index("ix_documents_tenant_status", "documents", ["tenant_id", "processing_status"])
    op.create_index("ix_documents_tenant_created", "documents", ["tenant_id", "created_at"])

    # Extend parse_jobs: email_id nullable, add document_id
    op.alter_column(
        "parse_jobs",
        "email_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "parse_jobs",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_parse_jobs_document_id",
        "parse_jobs",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_parse_jobs_document_id", "parse_jobs", ["document_id"])

    # Extend emission_reports: add document_id for document-based noon reports
    op.add_column(
        "emission_reports",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_emission_reports_document_id",
        "emission_reports",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Extend anomalies: document_id for document-based leakage audit
    op.alter_column(
        "anomalies",
        "email_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "anomalies",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_anomalies_document_id",
        "anomalies",
        "documents",
        ["document_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_anomalies_document_id", "anomalies", type_="foreignkey")
    op.drop_column("anomalies", "document_id")
    op.alter_column(
        "anomalies",
        "email_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_constraint("fk_emission_reports_document_id", "emission_reports", type_="foreignkey")
    op.drop_column("emission_reports", "document_id")

    op.drop_index("ix_parse_jobs_document_id", table_name="parse_jobs")
    op.drop_constraint("fk_parse_jobs_document_id", "parse_jobs", type_="foreignkey")
    op.drop_column("parse_jobs", "document_id")
    op.alter_column(
        "parse_jobs",
        "email_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_index("ix_documents_tenant_created", table_name="documents")
    op.drop_index("ix_documents_tenant_status", table_name="documents")
    op.drop_index("ix_documents_tenant_port_call", table_name="documents")
    op.drop_table("documents")
