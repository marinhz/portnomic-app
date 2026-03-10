import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SubscriptionPlan(str, Enum):
    """Subscription plan tier."""

    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription billing status."""

    ACTIVE = "active"
    TRIAL = "trial"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Subscription / billing
    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=SubscriptionPlan.STARTER.value,
    )
    subscription_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=SubscriptionStatus.TRIAL.value,
    )
    mypos_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mypos_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users = relationship("User", back_populates="tenant", lazy="selectin")
    roles = relationship("Role", back_populates="tenant", lazy="selectin")
    vessels = relationship("Vessel", back_populates="tenant", lazy="selectin")
    ports = relationship("Port", back_populates="tenant", lazy="selectin")
    llm_config = relationship(
        "TenantLlmConfig",
        back_populates="tenant",
        uselist=False,
        lazy="selectin",
    )
