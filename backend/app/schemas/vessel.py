import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VesselCreate(BaseModel):
    name: str
    imo: str | None = None
    mmsi: str | None = None
    vessel_type: str | None = None
    flag: str | None = None
    allowed_fuel_types: list[str] | None = None


class VesselUpdate(BaseModel):
    name: str | None = None
    imo: str | None = None
    mmsi: str | None = None
    vessel_type: str | None = None
    flag: str | None = None
    allowed_fuel_types: list[str] | None = None


class VesselResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    imo: str | None
    mmsi: str | None
    vessel_type: str | None
    flag: str | None
    allowed_fuel_types: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None
