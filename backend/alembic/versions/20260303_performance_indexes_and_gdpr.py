"""Performance indexes and GDPR fields

Revision ID: 20260303_perf_gdpr
Revises: c2d356803e41
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260303_perf_gdpr"
down_revision = "c2d356803e41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("correlation_id", sa.String(36), nullable=True))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_vessels_tenant_id", "vessels", ["tenant_id"], if_not_exists=True)
    op.create_index("ix_port_calls_tenant_status", "port_calls", ["tenant_id", "status"], if_not_exists=True)
    op.create_index("ix_port_calls_tenant_vessel", "port_calls", ["tenant_id", "vessel_id"], if_not_exists=True)
    op.create_index("ix_emails_tenant_status", "emails", ["tenant_id", "processing_status"], if_not_exists=True)
    op.create_index("ix_emails_tenant_received", "emails", ["tenant_id", "received_at"], if_not_exists=True)
    op.create_index("ix_parse_jobs_tenant_status", "parse_jobs", ["tenant_id", "status"], if_not_exists=True)
    op.create_index("ix_da_tenant_port_call", "disbursement_accounts", ["tenant_id", "port_call_id"], if_not_exists=True)
    op.create_index("ix_da_tenant_status", "disbursement_accounts", ["tenant_id", "status"], if_not_exists=True)
    op.create_index("ix_tariffs_tenant_port", "tariffs", ["tenant_id", "port_id"], if_not_exists=True)
    op.create_index("ix_tariffs_tenant_valid", "tariffs", ["tenant_id", "valid_from", "valid_to"], if_not_exists=True)
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id"], if_not_exists=True)
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], if_not_exists=True)
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"], if_not_exists=True)
    op.create_index(
        "ix_users_deleted_at",
        "users",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NOT NULL"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user", table_name="audit_logs")
    op.drop_index("ix_tariffs_tenant_valid", table_name="tariffs")
    op.drop_index("ix_tariffs_tenant_port", table_name="tariffs")
    op.drop_index("ix_da_tenant_status", table_name="disbursement_accounts")
    op.drop_index("ix_da_tenant_port_call", table_name="disbursement_accounts")
    op.drop_index("ix_parse_jobs_tenant_status", table_name="parse_jobs")
    op.drop_index("ix_emails_tenant_received", table_name="emails")
    op.drop_index("ix_emails_tenant_status", table_name="emails")
    op.drop_index("ix_port_calls_tenant_vessel", table_name="port_calls")
    op.drop_index("ix_port_calls_tenant_status", table_name="port_calls")
    op.drop_index("ix_vessels_tenant_id", table_name="vessels")

    op.drop_column("users", "deleted_at")
    op.drop_column("audit_logs", "correlation_id")
