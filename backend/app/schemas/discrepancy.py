"""Discrepancy schemas for Sentinel Operational Gap Engine."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DiscrepancyCreate(BaseModel):
    """Internal use by AuditEngine when persisting Sentinel audit findings."""

    tenant_id: uuid.UUID
    port_call_id: uuid.UUID
    source_documents: list[uuid.UUID] = []
    severity: str
    estimated_loss: Decimal | None = None
    description: str
    rule_id: str | None = None
    raw_evidence: dict | None = None


class SourceLabelResponse(BaseModel):
    """Human-readable source label for audit transparency."""

    id: uuid.UUID
    label: str


class DiscrepancyResponse(BaseModel):
    """API/frontend response; includes severity, description, estimated_loss, source_documents, source_labels."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    port_call_id: uuid.UUID
    severity: str
    description: str
    estimated_loss: Decimal | None = None
    source_documents: list[uuid.UUID]
    source_labels: list[SourceLabelResponse] = []  # Populated by API; not from model
    rule_id: str | None = None
    raw_evidence: dict | None = None
    created_at: datetime


class AuditReportResponse(BaseModel):
    """Response from Sentinel AuditEngine.compare_events."""

    discrepancies: list[DiscrepancyResponse]
    total_count: int
    by_severity: dict[str, int]
    by_rule: dict[str, int]
    rules_executed: list[str]
