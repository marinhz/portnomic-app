import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PortCreate(BaseModel):
    name: str
    code: str  # UN/LOCODE (e.g. NLRTM, SGSIN)
    country: str | None = None
    timezone: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class PortUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    country: str | None = None
    timezone: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class PortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str  # UN/LOCODE (e.g. NLRTM, SGSIN)
    country: str | None
    timezone: str | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
