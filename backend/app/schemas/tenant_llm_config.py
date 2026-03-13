"""Pydantic schemas for TenantLlmConfig."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.ssrf import validate_llm_base_url


def _validate_base_url(v: str | None) -> str | None:
    if v is not None and v.strip():
        validate_llm_base_url(v)
    return v


class TenantLlmConfigCreate(BaseModel):
    """Input for creating tenant LLM config. api_key is plain for input; encrypted on save."""

    api_key: str
    base_url: str | None = None
    model: str | None = None
    enabled: bool = True

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: str | None) -> str | None:
        return _validate_base_url(v)


class TenantLlmConfigUpdate(BaseModel):
    """Partial update for tenant LLM config. api_key optional."""

    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    enabled: bool | None = None

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: str | None) -> str | None:
        return _validate_base_url(v)


class AISettingsPut(BaseModel):
    """Upsert schema for PUT /settings/ai. api_key required when creating."""

    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    enabled: bool = True

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: str | None) -> str | None:
        return _validate_base_url(v)


class AITestBody(BaseModel):
    """Optional body for POST /settings/ai/test — test unsaved config before save."""

    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None

    @field_validator("base_url")
    @classmethod
    def check_base_url(cls, v: str | None) -> str | None:
        return _validate_base_url(v)


class PromptOverridePut(BaseModel):
    """Input for setting a custom prompt."""

    prompt_text: str
    version: str = "v1"


class TenantLlmConfigResponse(BaseModel):
    """Response schema. Never includes api_key; optional api_key_configured flag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    base_url: str | None = None
    model: str | None = None
    enabled: bool
    api_key_configured: bool = Field(
        default=False,
        description="True if an API key is stored (never exposes the key)",
    )
    created_at: datetime
    updated_at: datetime | None = None
