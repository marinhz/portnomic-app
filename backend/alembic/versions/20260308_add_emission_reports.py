"""Add emission_reports and fuel_entries tables

Revision ID: 20260308_emission
Revises: 20260307_sub
Create Date: 2026-03-08

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260308_emission"
down_revision = "20260307_sub"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "emission_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vessel_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("port_call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("distance_nm", sa.Float(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("schema_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vessel_id"], ["vessels.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["port_call_id"], ["port_calls.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["email_id"], ["emails.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emission_reports_tenant_id", "emission_reports", ["tenant_id"])
    op.create_index("ix_emission_reports_vessel_id", "emission_reports", ["vessel_id"])
    op.create_index("ix_emission_reports_report_date", "emission_reports", ["report_date"])
    op.create_index(
        "ix_emission_reports_tenant_vessel_date",
        "emission_reports",
        ["tenant_id", "vessel_id", "report_date"],
    )

    op.create_table(
        "fuel_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("emission_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fuel_type", sa.String(50), nullable=False),
        sa.Column("consumption_mt", sa.Float(), nullable=False),
        sa.Column("operational_status", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(
            ["emission_report_id"],
            ["emission_reports.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fuel_entries_emission_report_id",
        "fuel_entries",
        ["emission_report_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fuel_entries_emission_report_id", table_name="fuel_entries")
    op.drop_table("fuel_entries")
    op.drop_index("ix_emission_reports_tenant_vessel_date", table_name="emission_reports")
    op.drop_index("ix_emission_reports_report_date", table_name="emission_reports")
    op.drop_index("ix_emission_reports_vessel_id", table_name="emission_reports")
    op.drop_index("ix_emission_reports_tenant_id", table_name="emission_reports")
    op.drop_table("emission_reports")
