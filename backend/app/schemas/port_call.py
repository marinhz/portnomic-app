import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PortCallCreate(BaseModel):
    vessel_id: uuid.UUID
    port_id: uuid.UUID
    eta: datetime | None = None
    etd: datetime | None = None
    status: str = "scheduled"


class PortCallUpdate(BaseModel):
    vessel_id: uuid.UUID | None = None
    port_id: uuid.UUID | None = None
    eta: datetime | None = None
    etd: datetime | None = None
    status: str | None = None


class PortCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vessel_id: uuid.UUID
    port_id: uuid.UUID
    eta: datetime | None
    etd: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime | None
