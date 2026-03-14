"""Set demo tenant (admin@shipflow.ai) to enterprise plan for full rights

Revision ID: 20260313_demo_enterprise
Revises: 20260313_audit_status
Create Date: 2026-03-13

"""

import sqlalchemy as sa

from alembic import op

revision = "20260313_demo_enterprise"
down_revision = "20260313_audit_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set plan=enterprise for demo tenant (slug=demo) and for tenant of admin@shipflow.ai
    op.execute(
        """
        UPDATE tenants
        SET plan = 'enterprise'
        WHERE slug = 'demo'
           OR id IN (SELECT tenant_id FROM users WHERE LOWER(email) = 'admin@shipflow.ai')
        """
    )


def downgrade() -> None:
    # Revert demo tenant to starter (cannot know original plan)
    op.execute(
        """
        UPDATE tenants
        SET plan = 'starter'
        WHERE slug = 'demo'
           OR id IN (SELECT tenant_id FROM users WHERE LOWER(email) = 'admin@shipflow.ai')
        """
    )
