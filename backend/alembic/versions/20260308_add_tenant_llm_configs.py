"""Add tenant_llm_configs and tenant_prompt_overrides tables

Revision ID: 20260308_llm_config
Revises: 20260308_anomaly
Create Date: 2026-03-08

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20260308_llm_config"
down_revision = "20260308_anomaly"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_llm_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("api_key_encrypted", sa.Text, nullable=True),
        sa.Column("base_url", sa.String(512), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_tenant_llm_configs_tenant_id",
        "tenant_llm_configs",
        ["tenant_id"],
    )
    op.create_unique_constraint(
        "uq_tenant_llm_configs_tenant_id",
        "tenant_llm_configs",
        ["tenant_id"],
    )

    op.create_table(
        "tenant_prompt_overrides",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("parser_type", sa.String(32), nullable=False),
        sa.Column("prompt_text", sa.Text, nullable=False),
        sa.Column("version", sa.String(32), nullable=False, server_default="v1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_tenant_prompt_overrides_tenant_parser",
        "tenant_prompt_overrides",
        ["tenant_id", "parser_type"],
        unique=True,
    )
    op.create_index(
        "ix_tenant_prompt_overrides_tenant_id",
        "tenant_prompt_overrides",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_prompt_overrides_tenant_id", table_name="tenant_prompt_overrides")
    op.drop_index(
        "ix_tenant_prompt_overrides_tenant_parser",
        table_name="tenant_prompt_overrides",
    )
    op.drop_table("tenant_prompt_overrides")

    op.drop_constraint(
        "uq_tenant_llm_configs_tenant_id",
        "tenant_llm_configs",
        type_="unique",
    )
    op.drop_index("ix_tenant_llm_configs_tenant_id", table_name="tenant_llm_configs")
    op.drop_table("tenant_llm_configs")
