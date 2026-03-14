"""Anomaly schemas for AI Leakage Detector."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AnomalyCreate(BaseModel):
    """Internal use by AuditService when persisting detected discrepancies."""

    tenant_id: uuid.UUID
    email_id: uuid.UUID
    da_id: uuid.UUID | None = None
    port_call_id: uuid.UUID
    rule_id: str
    severity: str
    line_item_ref: str | None = None
    invoiced_value: Decimal | None = None
    expected_value: Decimal | None = None
    description: str
    raw_evidence: dict | None = None


class AnomalyResponse(BaseModel):
    """API/frontend response; includes rule_id, severity, description, values, line_item_ref."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email_id: uuid.UUID
    da_id: uuid.UUID | None = None
    port_call_id: uuid.UUID
    rule_id: str
    severity: str
    description: str
    line_item_ref: str | None = None
    invoiced_value: Decimal | None = None
    expected_value: Decimal | None = None
    raw_evidence: dict | None = None
    created_at: datetime
