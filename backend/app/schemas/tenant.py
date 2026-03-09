import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class TenantCreate(BaseModel):
    name: str
    slug: str
    initial_admin_email: EmailStr | None = None
    initial_admin_password: str | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not v or len(v) < 2:
            raise ValueError("Slug must be at least 2 characters")
        slug = v.lower().strip()
        if not all(c.isalnum() or c == "-" for c in slug):
            raise ValueError("Slug must be lowercase, alphanumeric with hyphens only")
        if slug[0] == "-" or slug[-1] == "-":
            raise ValueError("Slug cannot start or end with a hyphen")
        reserved = {"admin", "platform", "api", "system", "root", "shipflow"}
        if slug in reserved:
            raise ValueError(f"Slug '{slug}' is reserved")
        return slug


class TenantUpdate(BaseModel):
    name: str | None = None
    settings: dict | None = None
    plan: str | None = None

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str | None) -> str | None:
        if v is None:
            return v
        allowed = {"starter", "professional", "enterprise"}
        if v.lower() not in allowed:
            raise ValueError(f"Plan must be one of: {', '.join(allowed)}")
        return v.lower()


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    settings: dict | None
    created_at: datetime
    plan: str
    subscription_status: str
