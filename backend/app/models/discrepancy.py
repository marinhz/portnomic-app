"""Discrepancy model for Sentinel Operational Gap Engine — cross-source audit findings."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

DISCREPANCY_SEVERITIES = ("low", "medium", "high")
DISCREPANCY_RULE_IDS = ("S-001", "S-002", "S-003")


class Discrepancy(Base):
    """Sentinel audit finding: cross-source operational gap with estimated loss and source links."""

    __tablename__ = "discrepancies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    port_call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("port_calls.id", ondelete="CASCADE"), nullable=False
    )
    source_documents: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    estimated_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant = relationship("Tenant")
    port_call = relationship("PortCall")

    __table_args__ = (
        Index("ix_discrepancies_tenant_port_call", "tenant_id", "port_call_id"),
        Index("ix_discrepancies_tenant_severity", "tenant_id", "severity"),
    )
