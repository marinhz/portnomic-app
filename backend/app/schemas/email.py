import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.utils.email_headers import decode_mime_header


class EmailCreate(BaseModel):
    external_id: str
    subject: str | None = None
    sender: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    received_at: datetime | None = None
    port_call_id: uuid.UUID | None = None


class EmailUpdate(BaseModel):
    port_call_id: uuid.UUID | None = None


class _EmailSubjectSenderMixin:
    """Decode MIME encoded subject/sender for display."""

    @field_serializer("subject", "sender")
    def _decode_header(self, v: str | None) -> str | None:
        return decode_mime_header(v)


class EmailResponse(BaseModel, _EmailSubjectSenderMixin):
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


class EmailListResponse(BaseModel, _EmailSubjectSenderMixin):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    subject: str | None
    sender: str | None
    received_at: datetime | None
    processing_status: str
    retry_count: int
    created_at: datetime
    port_call_id: uuid.UUID | None = None
