import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class PortCallSource(str, Enum):
    AI = "ai"
    MANUAL = "manual"


class PortCallCreate(BaseModel):
    vessel_id: uuid.UUID
    port_id: uuid.UUID
    eta: datetime | None = None
    etd: datetime | None = None
    status: str = "scheduled"
    agent_assigned_id: uuid.UUID | None = None
    source: PortCallSource = PortCallSource.MANUAL


class PortCallUpdate(BaseModel):
    vessel_id: uuid.UUID | None = None
    port_id: uuid.UUID | None = None
    eta: datetime | None = None
    etd: datetime | None = None
    status: str | None = None
    agent_assigned_id: uuid.UUID | None = None
    source: PortCallSource | None = None


class DocumentCategory(str, Enum):
    """Document category for manual upload."""

    SOF = "sof"
    DA = "da"
    NOON_REPORT = "noon_report"


class DocumentResponse(BaseModel):
    """Document list item for port call documents tab."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    port_call_id: uuid.UUID
    filename: str
    category: str | None = None
    processing_status: str
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    """Response after manual document upload."""

    job_id: uuid.UUID | None = None  # None when status=already_processed
    document_id: uuid.UUID
    status: str = "pending"


class PortCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vessel_id: uuid.UUID
    port_id: uuid.UUID
    eta: datetime | None = None
    etd: datetime | None = None
    status: str
    agent_assigned_id: uuid.UUID | None = None
    source: str
    created_at: datetime
    updated_at: datetime | None = None
