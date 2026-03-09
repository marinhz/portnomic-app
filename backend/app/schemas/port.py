import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PortCreate(BaseModel):
    name: str
    code: str
    country: str | None = None
    timezone: str | None = None


class PortUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    country: str | None = None
    timezone: str | None = None


class PortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    country: str | None
    timezone: str | None
    created_at: datetime
