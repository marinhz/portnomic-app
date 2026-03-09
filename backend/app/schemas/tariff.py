import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TariffCreate(BaseModel):
    port_id: uuid.UUID
    name: str
    formula_config: dict
    valid_from: date
    valid_to: date | None = None


class TariffUpdate(BaseModel):
    name: str | None = None
    formula_config: dict | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class TariffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    port_id: uuid.UUID
    name: str
    version: int
    formula_config: dict
    valid_from: date
    valid_to: date | None
    created_at: datetime
    updated_at: datetime | None
