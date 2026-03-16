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
