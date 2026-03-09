"""Admin AI Settings API — LLM config and prompt overrides.

Task 10.4: REST API for company admins to manage LLM config and prompts.
Feature-gated to Professional and Enterprise plans.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.tenant_llm_config import (
    AISettingsPut,
    PromptOverridePut,
    TenantLlmConfigCreate,
    TenantLlmConfigResponse,
    TenantLlmConfigUpdate,
)
from app.services import audit as audit_svc
from app.services.limits import require_premium_ai
from app.services.llm_client import LlmConfigError, test_llm_connection
from app.services.prompt_override_svc import (
    list_prompt_overrides,
    reset_prompt_override,
    set_prompt_override,
)
from app.services.tenant_llm_config_svc import (
    create_tenant_llm_config,
    delete_tenant_llm_config,
    get_tenant_llm_config,
    get_tenant_llm_config_response,
    update_tenant_llm_config,
)

logger = logging.getLogger("shipflow")

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


async def _require_premium_and_admin(
    current_user: CurrentUser = Depends(
        RequirePermission("settings:write", allow_platform_admin=True)
    ),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> tuple[CurrentUser, uuid.UUID, AsyncSession]:
    """Dependency: require settings:write and premium plan."""
    await require_premium_ai(db, tenant_id)
    return current_user, tenant_id, db


# ── Config endpoints ───────────────────────────────────────────────────────────


@router.get("/ai", response_model=TenantLlmConfigResponse | None)
async def get_ai_config(
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> TenantLlmConfigResponse | None:
    """Get current AI config (masked; api_key_configured boolean only)."""
    _, tenant_id, db = dep
    return await get_tenant_llm_config_response(db, tenant_id)


@router.put("/ai", response_model=TenantLlmConfigResponse)
async def put_ai_config(
    body: AISettingsPut,
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> TenantLlmConfigResponse:
    """Create or update AI config (api_key, base_url, model, enabled)."""
    current_user, tenant_id, db = dep

    config = await get_tenant_llm_config(db, tenant_id)

    if config is not None:
        data = TenantLlmConfigUpdate(
            api_key=body.api_key,
            base_url=body.base_url,
            model=body.model,
            enabled=body.enabled,
        )
        updated = await update_tenant_llm_config(db, tenant_id, data)
        if updated is None:
            raise HTTPException(status_code=404, detail="Config not found")
        config = updated
    else:
        if not body.api_key or not body.api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="api_key is required when creating config",
            )
        data = TenantLlmConfigCreate(
            api_key=body.api_key,
            base_url=body.base_url,
            model=body.model,
            enabled=body.enabled,
        )
        config = await create_tenant_llm_config(db, tenant_id, data)

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="ai_config_updated",
        resource_type="tenant_llm_config",
        resource_id=str(config.id),
    )

    return await get_tenant_llm_config_response(db, tenant_id)


@router.delete("/ai", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_config(
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> None:
    """Remove AI config (soft: set enabled=false)."""
    current_user, tenant_id, db = dep

    deleted = await delete_tenant_llm_config(db, tenant_id)
    if deleted:
        await audit_svc.log_action(
            db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            action="ai_config_updated",
            resource_type="tenant_llm_config",
            payload={"action": "disabled"},
        )


# ── Prompt override endpoints ──────────────────────────────────────────────────


@router.get("/ai/prompts")
async def get_ai_prompts(
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> list[dict[str, str]]:
    """List prompt overrides (parser_type, prompt_text, version)."""
    _, tenant_id, db = dep
    return await list_prompt_overrides(db, tenant_id)


@router.put("/ai/prompts/{parser_type}")
async def put_ai_prompt(
    parser_type: str,
    body: PromptOverridePut,
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> dict[str, str]:
    """Set custom prompt for parser_type."""
    current_user, tenant_id, db = dep

    try:
        override = await set_prompt_override(
            db, tenant_id, parser_type, body.prompt_text, body.version
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="ai_prompt_updated",
        resource_type="tenant_prompt_override",
        resource_id=str(override.id),
    )

    return {
        "parser_type": override.parser_type,
        "prompt_text": override.prompt_text,
        "version": override.version,
    }


@router.post("/ai/prompts/{parser_type}/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_ai_prompt(
    parser_type: str,
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> None:
    """Reset prompt to default for parser_type."""
    current_user, tenant_id, db = dep

    try:
        deleted = await reset_prompt_override(db, tenant_id, parser_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if deleted:
        await audit_svc.log_action(
            db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            action="ai_prompt_updated",
            resource_type="tenant_prompt_override",
            payload={"action": "reset", "parser_type": parser_type},
        )


# ── Test connection (optional) ──────────────────────────────────────────────────


@router.post("/ai/test")
async def test_ai_connection(
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> dict[str, str]:
    """Test LLM connection with minimal prompt. Returns 200 if OK."""
    _, tenant_id, db = dep

    try:
        await test_llm_connection(tenant_id=tenant_id, db=db)
    except LlmConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "llm_config_error", "message": str(e)},
        )
    except Exception as e:
        logger.warning("AI test connection failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "llm_connection_error", "message": str(e)},
        )

    return {"status": "ok", "message": "Connection successful"}
