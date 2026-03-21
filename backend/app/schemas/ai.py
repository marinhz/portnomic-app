import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParseRequest(BaseModel):
    email_id: uuid.UUID


class ParseJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email_id: uuid.UUID
    status: str
    result: dict | None
    error_message: str | None
    prompt_version: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ParsedLineItem(BaseModel):
    description: str
    amount: float | None = None  # LLM may omit when unparseable
    currency: str = "USD"
    quantity: float | None = None
    unit_price: float | None = None
    service_date: str | None = None  # ISO 8601 date/time for LD-001, LD-003


class ParsedEmailResult(BaseModel):
    vessel_name: str | None = None
    vessel_imo: str | None = None
    port_name: str | None = None
    port_code: str | None = None
    eta: str | None = None
    etd: str | None = None
    line_items: list[ParsedLineItem] = Field(default_factory=list)
    total_amount: float | None = None
    currency: str | None = None
    summary: str | None = None


class EmailStatusUpdate(BaseModel):
    processing_status: str | None = None
    error_reason: str | None = None


class WebhookInboundEmail(BaseModel):
    from_email: str = Field(alias="from")
    to: str
    subject: str | None = None
    text: str | None = None
    html: str | None = None
    message_id: str | None = None

    model_config = ConfigDict(populate_by_name=True)
