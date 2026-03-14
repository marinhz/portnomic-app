import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

DA_STATUSES = ("draft", "pending_approval", "approved", "sent")
DA_TYPES = ("proforma", "final")

VALID_TRANSITIONS = {
    "draft": ("pending_approval", "approved"),
    "pending_approval": ("approved",),
    "approved": ("sent",),
    "sent": (),
}


class DisbursementAccount(Base):
    __tablename__ = "disbursement_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    port_call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("port_calls.id", ondelete="CASCADE"), nullable=False
    )
    tariff_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tariffs.id", ondelete="SET NULL"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    line_items: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    totals: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    pdf_blob_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    audit_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )  # completed | pending_manual_review | failed

    tenant = relationship("Tenant")
    port_call = relationship("PortCall")
    tariff = relationship("Tariff")

    __table_args__ = (
        Index("ix_da_tenant_port_call", "tenant_id", "port_call_id"),
        Index("ix_da_tenant_status", "tenant_id", "status"),
        Index("ix_da_tenant_created", "tenant_id", "created_at"),
    )
