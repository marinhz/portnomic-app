"""Add audit_status to emails and disbursement_accounts (Task 12.4)

Revision ID: 20260313_audit_status
Revises: 20260313_leakage_anomalies
Create Date: 2026-03-13

"""

import sqlalchemy as sa

from alembic import op

revision = "20260313_audit_status"
down_revision = "20260313_leakage_anomalies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "emails",
        sa.Column("audit_status", sa.String(30), nullable=True),
    )
    op.add_column(
        "disbursement_accounts",
        sa.Column("audit_status", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("disbursement_accounts", "audit_status")
    op.drop_column("emails", "audit_status")
