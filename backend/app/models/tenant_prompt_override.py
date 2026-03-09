"""Tenant prompt overrides for custom parser prompts."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ParserType(str, Enum):
    """Parser type for prompt overrides."""

    DA_EMAIL = "da_email"
    EMISSION_REPORT = "emission_report"


class TenantPromptOverride(Base):
    """Per-tenant custom prompt for a parser type."""

    __tablename__ = "tenant_prompt_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    parser_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    tenant = relationship("Tenant")

    __table_args__ = (
        Index(
            "ix_tenant_prompt_overrides_tenant_parser",
            "tenant_id",
            "parser_type",
            unique=True,
        ),
        Index("ix_tenant_prompt_overrides_tenant_id", "tenant_id"),
    )
