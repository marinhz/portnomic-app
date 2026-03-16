import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class DALineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    amount: float
    currency: str = "USD"


class DATotals(BaseModel):
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    currency: str = "USD"


class DAGenerateRequest(BaseModel):
    port_call_id: uuid.UUID
    type: Literal["proforma", "final"]


class DASendRequest(BaseModel):
    to_addresses: list[str] | None = None


class DAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    port_call_id: uuid.UUID
    tariff_id: uuid.UUID | None
    version: int
    type: str
    status: str
    line_items: list[DALineItem]
    totals: DATotals
    currency: str
    pdf_blob_id: str | None
    created_at: datetime
    updated_at: datetime | None
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    sent_at: datetime | None


class DAListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    port_call_id: uuid.UUID
    version: int
    type: str
    status: str
    currency: str
    created_at: datetime
    approved_at: datetime | None
    sent_at: datetime | None
    has_anomalies: bool | None = None  # Only present when tenant has Leakage Detector
