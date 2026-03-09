"""Emission report and fuel entry models for EU ETS / FuelEU Maritime compliance."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# Report verification status: verified (no anomalies), flagged (has anomalies), failed (critical)
REPORT_STATUS_VERIFIED = "verified"
REPORT_STATUS_FLAGGED = "flagged"
REPORT_STATUS_FAILED = "failed"


class EmissionReport(Base):
    """Tenant-scoped emission report from Noon/Bunker reports."""

    __tablename__ = "emission_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    vessel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False
    )
    port_call_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("port_calls.id", ondelete="SET NULL"),
        nullable=True,
    )
    email_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="SET NULL"),
        nullable=True,
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    distance_nm: Mapped[float | None] = mapped_column(Float, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=REPORT_STATUS_VERIFIED
    )
    anomaly_flags: Mapped[list | None] = mapped_column(
        JSONB, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    tenant = relationship("Tenant")
    vessel = relationship("Vessel")
    port_call = relationship("PortCall")
    email = relationship("Email")
    fuel_entries = relationship(
        "FuelEntry",
        back_populates="emission_report",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_emission_reports_tenant_id", "tenant_id"),
        Index("ix_emission_reports_vessel_id", "vessel_id"),
        Index("ix_emission_reports_report_date", "report_date"),
        Index("ix_emission_reports_tenant_vessel_date", "tenant_id", "vessel_id", "report_date"),
    )


class FuelEntry(Base):
    """Individual fuel consumption entry within an emission report."""

    __tablename__ = "fuel_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    emission_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emission_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    fuel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    consumption_mt: Mapped[float] = mapped_column(Float, nullable=False)
    operational_status: Mapped[str] = mapped_column(String(50), nullable=False)

    emission_report = relationship("EmissionReport", back_populates="fuel_entries")

    __table_args__ = (
        Index("ix_fuel_entries_emission_report_id", "emission_report_id"),
    )
