import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    requires_mfa: bool = False
    mfa_token: str | None = None


class MfaRequest(BaseModel):
    mfa_token: str
    code: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    refresh_token: str | None = None  # Returned on refresh when rotation is enabled


class TokenPayload(BaseModel):
    sub: str
    tenant_id: str
    role_id: str
    permissions: list[str]
    exp: int
    type: str


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class CurrentUser(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    role_id: uuid.UUID
    role_name: str | None = None
    permissions: list[str]
    mfa_enabled: bool = False
    is_platform_admin: bool = False
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class MfaConfirmRequest(BaseModel):
    code: str


class MfaDisableRequest(BaseModel):
    password: str | None = None
    code: str | None = None
