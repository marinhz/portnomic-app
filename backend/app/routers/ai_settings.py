"""Admin AI Settings API — LLM config and prompt overrides.

Task 10.4: REST API for company admins to manage LLM config and prompts.
Feature-gated to Professional and Enterprise plans.
"""

import logging
import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.tenant_llm_config import (
    AISettingsPut,
    AITestBody,
    PromptOverridePut,
    TenantLlmConfigCreate,
    TenantLlmConfigResponse,
    TenantLlmConfigUpdate,
)
from app.services import audit as audit_svc
from app.services.limits import require_premium_ai
from app.services.llm_client import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    LlmConfigError,
    RateLimitError,
    test_llm_connection,
)
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
    """Dependency: require settings:write and premium plan (or platform admin)."""
    await require_premium_ai(
        db, tenant_id, is_platform_admin=current_user.is_platform_admin or False
    )
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


def _ai_test_error(code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    """Raise HTTPException with structured error for frontend."""
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


@router.post("/ai/test")
async def test_ai_connection(
    body: AITestBody | None = Body(None),
    dep: tuple[CurrentUser, uuid.UUID, AsyncSession] = Depends(_require_premium_and_admin),
) -> dict[str, str]:
    """Test LLM connection with minimal prompt.

    Accepts optional body with api_key, base_url, model to test unsaved config
    (credentials from form before save). If provided, uses those values instead
    of DB/platform config.
    """
    _, tenant_id, db = dep

    api_key = body.api_key if body else None
    base_url = body.base_url if body else None
    model = body.model if body else None

    try:
        used_model, _ = await test_llm_connection(
            tenant_id=tenant_id,
            db=db,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
    except LlmConfigError as e:
        _ai_test_error("llm_config_error", str(e))
    except APIConnectionError:
        _ai_test_error(
            "connection_error",
            "Cannot reach AI service. Check base URL and network.",
            status.HTTP_502_BAD_GATEWAY,
        )
    except APITimeoutError:
        _ai_test_error(
            "timeout_error",
            "Request timed out. AI service may be slow or unreachable.",
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
    except RateLimitError:
        _ai_test_error("rate_limit_error", "Rate limit exceeded. Try again later.")
    except AuthenticationError:
        _ai_test_error("auth_error", "Invalid API key. Check your credentials.")
    except ValueError as e:
        _ai_test_error("invalid_url", str(e))
    except Exception as e:
        logger.warning("AI test connection failed: %s", e)
        _ai_test_error(
            "llm_connection_error",
            str(e),
            status.HTTP_502_BAD_GATEWAY,
        )

    return {
        "status": "ok",
        "message": f"Connected to {used_model}",
        "model": used_model,
    }
