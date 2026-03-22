"""Add invoice_number to disbursement_accounts for DA deduplication

Revision ID: 20260321_da_invoice
Revises: 20260321_documents
Create Date: 2026-03-21

Used to match DA by Invoice Number when multiple documents uploaded for same port call.
One Port Call = One Final DA; additional files trigger audit, not duplication.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260321_da_invoice"
down_revision = "20260321_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "disbursement_accounts",
        sa.Column("invoice_number", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("disbursement_accounts", "invoice_number")
