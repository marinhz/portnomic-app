import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmailCreate(BaseModel):
    external_id: str
    subject: str | None = None
    sender: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    received_at: datetime | None = None
    port_call_id: uuid.UUID | None = None


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    port_call_id: uuid.UUID | None
    external_id: str
    subject: str | None
    sender: str | None
    received_at: datetime | None
    processing_status: str
    ai_raw_output: dict | None
    error_reason: str | None
    prompt_version: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime | None
    emission_report_id: uuid.UUID | None = None


class EmailListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    subject: str | None
    sender: str | None
    received_at: datetime | None
    processing_status: str
    retry_count: int
    created_at: datetime
