"""CRUD for tenant prompt overrides."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_prompt_override import ParserType, TenantPromptOverride

__all__ = [
    "list_prompt_overrides",
    "set_prompt_override",
    "reset_prompt_override",
]


async def list_prompt_overrides(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> list[dict[str, str]]:
    """List all prompt overrides for tenant. Returns parser_type, prompt_text, version."""
    stmt = select(TenantPromptOverride).where(
        TenantPromptOverride.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    overrides = result.scalars().all()
    return [
        {
            "parser_type": o.parser_type,
            "prompt_text": o.prompt_text,
            "version": o.version,
        }
        for o in overrides
    ]


async def set_prompt_override(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    parser_type: str,
    prompt_text: str,
    version: str = "v1",
) -> TenantPromptOverride:
    """Create or update prompt override for parser_type."""
    if parser_type not in (p.value for p in ParserType):
        raise ValueError(f"Unknown parser_type: {parser_type}")

    stmt = select(TenantPromptOverride).where(
        TenantPromptOverride.tenant_id == tenant_id,
        TenantPromptOverride.parser_type == parser_type,
    )
    result = await db.execute(stmt)
    override = result.scalar_one_or_none()

    if override is not None:
        override.prompt_text = prompt_text
        override.version = version
        await db.flush()
        await db.refresh(override)
        return override

    override = TenantPromptOverride(
        tenant_id=tenant_id,
        parser_type=parser_type,
        prompt_text=prompt_text,
        version=version,
    )
    db.add(override)
    await db.flush()
    await db.refresh(override)
    return override


async def reset_prompt_override(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    parser_type: str,
) -> bool:
    """Delete prompt override to restore default. Returns True if deleted."""
    if parser_type not in (p.value for p in ParserType):
        raise ValueError(f"Unknown parser_type: {parser_type}")

    stmt = select(TenantPromptOverride).where(
        TenantPromptOverride.tenant_id == tenant_id,
        TenantPromptOverride.parser_type == parser_type,
    )
    result = await db.execute(stmt)
    override = result.scalar_one_or_none()

    if override is None:
        return False

    await db.delete(override)
    await db.flush()
    return True
