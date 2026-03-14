"""Anomaly model for AI Leakage Detector — detected discrepancies from leakage audit."""

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

ANOMALY_SEVERITIES = ("low", "medium", "high", "critical")
ANOMALY_RULE_IDS = ("LD-001", "LD-002", "LD-003", "LD-004")


class Anomaly(Base):
    """Detected discrepancy from leakage audit, linked to Email and DA for traceability."""

    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), nullable=False
    )
    da_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("disbursement_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    port_call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("port_calls.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    line_item_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    invoiced_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    expected_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    raw_evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant = relationship("Tenant")
    email = relationship("Email")
    disbursement_account = relationship("DisbursementAccount")
    port_call = relationship("PortCall")

    __table_args__ = (
        Index("ix_anomalies_tenant_email", "tenant_id", "email_id"),
        Index("ix_anomalies_tenant_da", "tenant_id", "da_id"),
    )
