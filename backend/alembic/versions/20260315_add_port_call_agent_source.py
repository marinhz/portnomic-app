"""Add agent_assigned_id and source to port_calls table

Revision ID: 20260315_port_call_agent_source
Revises: 20260315_port_coords
Create Date: 2026-03-15

"""

import sqlalchemy as sa

from alembic import op

revision = "20260315_port_call_agent_source"
down_revision = "20260315_port_coords"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "port_calls",
        sa.Column("agent_assigned_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_port_calls_agent_assigned_id_users",
        "port_calls",
        "users",
        ["agent_assigned_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "port_calls",
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_port_calls_agent_assigned_id_users",
        "port_calls",
        type_="foreignkey",
    )
    op.drop_column("port_calls", "source")
    op.drop_column("port_calls", "agent_assigned_id")
