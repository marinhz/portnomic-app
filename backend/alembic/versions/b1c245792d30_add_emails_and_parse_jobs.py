"""add emails and parse_jobs

Revision ID: b1c245792d30
Revises: a0b134681b29
Create Date: 2026-03-03 22:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = 'b1c245792d30'
down_revision: Union[str, None] = 'a0b134681b29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'emails',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('port_call_id', sa.UUID(), nullable=True),
        sa.Column('external_id', sa.String(length=512), nullable=False),
        sa.Column('subject', sa.String(length=1000), nullable=True),
        sa.Column('sender', sa.String(length=320), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('ai_raw_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_reason', sa.Text(), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['port_call_id'], ['port_calls.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_emails_tenant_external_id', 'emails', ['tenant_id', 'external_id'], unique=True)
    op.create_index('ix_emails_tenant_status', 'emails', ['tenant_id', 'processing_status'], unique=False)
    op.create_index('ix_emails_tenant_created', 'emails', ['tenant_id', 'created_at'], unique=False)

    op.create_table(
        'parse_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('email_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('prompt_version', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_parse_jobs_tenant_status', 'parse_jobs', ['tenant_id', 'status'], unique=False)
    op.create_index('ix_parse_jobs_email_id', 'parse_jobs', ['email_id'], unique=False)
    op.create_index('ix_parse_jobs_tenant_created', 'parse_jobs', ['tenant_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_parse_jobs_tenant_created', table_name='parse_jobs')
    op.drop_index('ix_parse_jobs_email_id', table_name='parse_jobs')
    op.drop_index('ix_parse_jobs_tenant_status', table_name='parse_jobs')
    op.drop_table('parse_jobs')
    op.drop_index('ix_emails_tenant_created', table_name='emails')
    op.drop_index('ix_emails_tenant_status', table_name='emails')
    op.drop_index('ix_emails_tenant_external_id', table_name='emails')
    op.drop_table('emails')
