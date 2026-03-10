import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Vessel(Base):
    __tablename__ = "vessels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    imo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mmsi: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vessel_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    allowed_fuel_types: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    tenant = relationship("Tenant", back_populates="vessels")
    port_calls = relationship("PortCall", back_populates="vessel", lazy="selectin")

    __table_args__ = (
        Index("ix_vessels_tenant_name", "tenant_id", "name"),
        Index("ix_vessels_tenant_imo", "tenant_id", "imo"),
        Index("ix_vessels_tenant_created", "tenant_id", "created_at"),
    )
