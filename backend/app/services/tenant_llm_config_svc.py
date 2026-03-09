"""Tenant LLM config service: CRUD with encryption for API keys."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tenant_llm_config import TenantLlmConfig
from app.schemas.tenant_llm_config import (
    TenantLlmConfigCreate,
    TenantLlmConfigResponse,
    TenantLlmConfigUpdate,
)
from app.services.encryption import decrypt_api_key, encrypt_api_key

logger = logging.getLogger("shipflow.tenant_llm_config")

__all__ = [
    "create_tenant_llm_config",
    "update_tenant_llm_config",
    "delete_tenant_llm_config",
    "get_tenant_llm_config",
    "get_tenant_llm_config_response",
    "get_decrypted_llm_credentials",
]


async def create_tenant_llm_config(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: TenantLlmConfigCreate,
) -> TenantLlmConfig:
    """Create tenant LLM config. Encrypts api_key before storing."""
    api_key_encrypted = encrypt_api_key(data.api_key) if data.api_key else None

    config = TenantLlmConfig(
        tenant_id=tenant_id,
        api_key_encrypted=api_key_encrypted,
        base_url=data.base_url,
        model=data.model,
        enabled=data.enabled,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)
    return config


async def update_tenant_llm_config(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: TenantLlmConfigUpdate,
) -> TenantLlmConfig | None:
    """Update tenant LLM config. Encrypts api_key if provided."""
    config = await get_tenant_llm_config(db, tenant_id)
    if config is None:
        return None

    if data.api_key is not None:
        config.api_key_encrypted = encrypt_api_key(data.api_key) if data.api_key else None
    if data.base_url is not None:
        config.base_url = data.base_url
    if data.model is not None:
        config.model = data.model
    if data.enabled is not None:
        config.enabled = data.enabled

    await db.flush()
    await db.refresh(config)
    return config


async def delete_tenant_llm_config(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> bool:
    """Soft-delete tenant LLM config (set enabled=false). Returns True if config existed."""
    config = await get_tenant_llm_config(db, tenant_id)
    if config is None:
        return False
    config.enabled = False
    await db.flush()
    return True


async def get_tenant_llm_config(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> TenantLlmConfig | None:
    """Fetch TenantLlmConfig by tenant_id. Never returns decrypted key."""
    stmt = select(TenantLlmConfig).where(TenantLlmConfig.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tenant_llm_config_response(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> TenantLlmConfigResponse | None:
    """Fetch config as response schema. Never includes api_key."""
    config = await get_tenant_llm_config(db, tenant_id)
    if config is None:
        return None
    return TenantLlmConfigResponse(
        id=config.id,
        tenant_id=config.tenant_id,
        base_url=config.base_url,
        model=config.model,
        enabled=config.enabled,
        api_key_configured=config.api_key_configured,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def get_decrypted_llm_credentials(
    config: TenantLlmConfig | None,
) -> tuple[str, str, str] | None:
    """Decrypt and return (api_key, base_url, model) for LLM client building.

    Call only when constructing the LLM client. Never expose in API response.
    Returns None if config missing, disabled, or decryption fails (key invalid).
    """
    if config is None or not config.enabled:
        return None
    if not config.api_key_encrypted:
        return None

    try:
        api_key = decrypt_api_key(config.api_key_encrypted)
    except ValueError:
        logger.warning("Tenant LLM config decryption failed; treating as key invalid")
        return None

    base_url = config.base_url or settings.llm_api_url
    model = config.model or settings.llm_model
    return (api_key, base_url, model)
