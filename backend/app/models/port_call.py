import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PortCall(Base):
    __tablename__ = "port_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    vessel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vessels.id", ondelete="CASCADE"), nullable=False
    )
    port_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ports.id", ondelete="CASCADE"), nullable=False
    )
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    etd: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    tenant = relationship("Tenant")
    vessel = relationship("Vessel", back_populates="port_calls")
    port = relationship("Port", back_populates="port_calls")

    __table_args__ = (
        Index("ix_port_calls_tenant_vessel", "tenant_id", "vessel_id"),
        Index("ix_port_calls_tenant_status", "tenant_id", "status"),
        Index("ix_port_calls_tenant_created", "tenant_id", "created_at"),
    )
