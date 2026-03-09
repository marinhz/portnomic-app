import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    port_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("port_calls.id", ondelete="SET NULL"),
        nullable=True,
    )
    external_id: Mapped[str] = mapped_column(String(512), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sender: Mapped[str | None] = mapped_column(String(320), nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    processing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    ai_raw_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
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
        "ParseJob", back_populates="email", lazy="selectin", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_emails_tenant_external_id", "tenant_id", "external_id", unique=True),
        Index("ix_emails_tenant_status", "tenant_id", "processing_status"),
        Index("ix_emails_tenant_created", "tenant_id", "created_at"),
    )
