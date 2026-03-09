import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, SingleResponse
from app.schemas.integrations import ImapConnectionCreate, MailConnectionResponse
from app.services import audit as audit_svc
from app.services import mail_connection as mc_svc

logger = logging.getLogger("shipflow.integrations")

router = APIRouter(prefix="/api/v1/integrations/email", tags=["integrations"])


# ── OAuth initiate ────────────────────────────────────────────────────────────


@router.get("/connect")
async def initiate_oauth(
    provider: str = Query(..., pattern="^(gmail|outlook)$"),
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
) -> dict:
    state_data = {
        "tenant_id": str(tenant_id),
        "user_id": str(current_user.id),
        "provider": provider,
    }
    state = mc_svc.encrypt_state(state_data)

    if provider == "gmail":
        url = mc_svc.build_google_auth_url(state)
    else:
        url = mc_svc.build_microsoft_auth_url(state)

    return {"url": url}


# ── OAuth callback (public — state ties to tenant) ───────────────────────────


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    from app.config import settings as app_settings

    base_url = app_settings.oauth_frontend_success_url

    if error:
        return RedirectResponse(
            url=f"{base_url}?error={error}", status_code=status.HTTP_302_FOUND
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{base_url}?error=missing_params", status_code=status.HTTP_302_FOUND
        )

    try:
        state_data = mc_svc.decrypt_state(state)
    except Exception:
        return RedirectResponse(
            url=f"{base_url}?error=invalid_state", status_code=status.HTTP_302_FOUND
        )

    tenant_id = uuid.UUID(state_data["tenant_id"])
    user_id = uuid.UUID(state_data["user_id"])
    provider = state_data["provider"]

    try:
        if provider == "gmail":
            token_data = await mc_svc.exchange_google_code(code)
        elif provider == "outlook":
            token_data = await mc_svc.exchange_microsoft_code(code)
        else:
            return RedirectResponse(
                url=f"{base_url}?error=unknown_provider",
                status_code=status.HTTP_302_FOUND,
            )
    except Exception:
        logger.exception("Code exchange failed for provider=%s", provider)
        return RedirectResponse(
            url=f"{base_url}?error=exchange_failed",
            status_code=status.HTTP_302_FOUND,
        )

    conn = await mc_svc.upsert_oauth_connection(db, tenant_id, provider, token_data)

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="mail_connection_added",
        resource_type="mail_connection",
        resource_id=str(conn.id),
        payload={"provider": provider, "display_email": conn.display_email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return RedirectResponse(
        url=f"{base_url}?email=connected&provider={provider}",
        status_code=status.HTTP_302_FOUND,
    )


# ── List connections ──────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=SingleResponse[list[MailConnectionResponse]],
)
async def list_connections(
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[list[MailConnectionResponse]]:
    connections = await mc_svc.list_connections(db, tenant_id)
    return SingleResponse(
        data=[MailConnectionResponse.model_validate(c) for c in connections]
    )


# ── Sync now (fetch new mail from connected mailboxes) ────────────────────────


@router.post("/sync")
async def sync_now(
    full: bool = Query(default=False, description="Reset sync state and re-fetch recent emails"),
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.oauth_ingest import poll_tenant_connections

    if full:
        await mc_svc.reset_sync_state_for_tenant(db, tenant_id)
    count = await poll_tenant_connections(db, tenant_id)
    return {"ingested": count}


# ── Delete (disconnect) ──────────────────────────────────────────────────────


@router.delete(
    "/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def disconnect(
    connection_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    conn = await mc_svc.get_connection(db, tenant_id, connection_id)
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "CONNECTION_NOT_FOUND",
                    "message": "Mail connection not found",
                }
            },
        )

    provider = conn.provider
    display_email = conn.display_email
    await mc_svc.delete_connection(db, tenant_id, connection_id)

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="mail_connection_removed",
        resource_type="mail_connection",
        resource_id=str(connection_id),
        payload={"provider": provider, "display_email": display_email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


# ── IMAP connection (Task 6.8) ───────────────────────────────────────────────


@router.post(
    "/imap",
    response_model=SingleResponse[MailConnectionResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def add_imap_connection(
    body: ImapConnectionCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[MailConnectionResponse]:
    conn = await mc_svc.create_imap_connection(
        db,
        tenant_id,
        imap_host=body.imap_host,
        imap_port=body.imap_port,
        imap_user=body.imap_user,
        imap_password=body.imap_password,
    )

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="mail_connection_added",
        resource_type="mail_connection",
        resource_id=str(conn.id),
        payload={"provider": "imap", "display_email": conn.display_email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SingleResponse(data=MailConnectionResponse.model_validate(conn))
