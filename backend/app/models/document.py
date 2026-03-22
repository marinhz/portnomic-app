"""Document model for manual uploads and other non-email sources."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DocumentSourceType:
    """Source type for documents."""

    MANUAL_UPLOAD = "manual_upload"
    EMAIL = "email"  # Future: documents extracted from emails
    API = "api"  # Future: Port Authority API, etc.


class Document(Base):
    """Tenant-scoped document from manual upload or other source.

    Manual uploads create Document rows only (never Email). ParseWorker
    processes documents and links parsed data to the given port_call_id.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    port_call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("port_calls.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DocumentSourceType.MANUAL_UPLOAD
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)  # sof, da, noon_report
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # Extracted text
    processing_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    ai_raw_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    audit_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    tenant = relationship("Tenant")
    port_call = relationship("PortCall")
    parse_jobs = relationship(
        "ParseJob", back_populates="document", lazy="selectin", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_documents_tenant_port_call", "tenant_id", "port_call_id"),
        Index("ix_documents_tenant_status", "tenant_id", "processing_status"),
        Index("ix_documents_tenant_created", "tenant_id", "created_at"),
        Index("ix_documents_tenant_content_hash", "tenant_id", "content_hash"),
    )
