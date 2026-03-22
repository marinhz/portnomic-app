"""Add index on documents.content_hash for deduplication lookups

Revision ID: 20260321_content_hash_idx
Revises: 20260321_da_invoice
Create Date: 2026-03-21

Enables fast lookup when checking for duplicate file content before ingestion.
Prevents redundant AI parsing and Sentinel audits for identical uploads.
"""

from alembic import op

revision = "20260321_content_hash_idx"
down_revision = "20260321_da_invoice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_documents_tenant_content_hash",
        "documents",
        ["tenant_id", "content_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_tenant_content_hash", table_name="documents")
