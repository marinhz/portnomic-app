import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role_id: uuid.UUID
    mfa_enabled: bool = False


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role_id: uuid.UUID | None = None
    is_active: bool | None = None
    mfa_enabled: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_active: bool
    mfa_enabled: bool
    role_id: uuid.UUID
    created_at: datetime
    last_login_at: datetime | None


class RoleCreate(BaseModel):
    name: str
    permissions: list[str]


class RoleUpdate(BaseModel):
    name: str | None = None
    permissions: list[str] | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    permissions: list[str]
    created_at: datetime
