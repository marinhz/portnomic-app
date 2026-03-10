import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.disbursement_account import (
    DAGenerateRequest,
    DAListResponse,
    DAResponse,
    DASendRequest,
)
from app.services import audit as audit_svc
from app.services import disbursement_account as da_svc
from app.services.da_worker import process_da_send
from app.services.storage import get_blob

router = APIRouter(prefix="/api/v1/da", tags=["disbursement-accounts"])

_background_tasks: set[asyncio.Task] = set()  # prevent GC of fire-and-forget tasks


@router.get(
    "",
    response_model=PaginatedResponse[DAListResponse],
)
async def list_das(
    port_call_id: uuid.UUID | None = None,
    da_status: str | None = None,
    page: int = 1,
    per_page: int = 20,
    current_user: CurrentUser = Depends(RequirePermission("da:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DAListResponse]:
    das, total = await da_svc.list_das(db, tenant_id, port_call_id, da_status, page, per_page)
    return PaginatedResponse(
        data=[DAListResponse.model_validate(d) for d in das],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "/generate",
    response_model=SingleResponse[DAResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"description": "Plan limit exceeded (upgrade_required)"}, 404: {"model": ErrorResponse}},
)
async def generate_da(
    body: DAGenerateRequest,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("da:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DAResponse]:
    try:
        da = await da_svc.generate_da(db, tenant_id, body.port_call_id, body.type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": str(exc)}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="generate",
        resource_type="disbursement_account",
        resource_id=str(da.id),
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=DAResponse.model_validate(da))


@router.get(
    "/{da_id}",
    response_model=SingleResponse[DAResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_da(
    da_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("da:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DAResponse]:
    da = await da_svc.get_da(db, tenant_id, da_id)
    if da is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DA_NOT_FOUND", "message": "Disbursement account not found"}},
        )
    return SingleResponse(data=DAResponse.model_validate(da))


@router.get(
    "/{da_id}/pdf",
    responses={404: {"model": ErrorResponse}},
)
async def get_da_pdf(
    da_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("da:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    da = await da_svc.get_da(db, tenant_id, da_id)
    if da is None or not da.pdf_blob_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PDF_NOT_FOUND", "message": "PDF not available for this DA"}},
        )
    pdf_data = await get_blob(da.pdf_blob_id)
    if pdf_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PDF_NOT_FOUND", "message": "PDF file not found in storage"}},
        )
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="DA_{str(da_id)[:8]}.pdf"'},
    )


@router.post(
    "/{da_id}/approve",
    response_model=SingleResponse[DAResponse],
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def approve_da(
    da_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("da:approve")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DAResponse]:
    try:
        da = await da_svc.approve_da(db, tenant_id, da_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_TRANSITION", "message": str(exc)}},
        )
    if da is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DA_NOT_FOUND", "message": "Disbursement account not found"}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="approve",
        resource_type="disbursement_account",
        resource_id=str(da.id),
        payload={"status": da.status},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=DAResponse.model_validate(da))


@router.post(
    "/{da_id}/send",
    status_code=status.HTTP_202_ACCEPTED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def send_da(
    da_id: uuid.UUID,
    body: DASendRequest | None = None,
    request: Request = None,
    current_user: CurrentUser = Depends(RequirePermission("da:send")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    da = await da_svc.get_da(db, tenant_id, da_id)
    if da is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DA_NOT_FOUND", "message": "Disbursement account not found"}},
        )
    if da.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_STATUS", "message": f"DA must be approved to send (current: {da.status})"}},
        )

    to_addresses = body.to_addresses if body and body.to_addresses else []

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="send",
        resource_type="disbursement_account",
        resource_id=str(da.id),
        payload={"to_addresses": to_addresses},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    task = asyncio.create_task(process_da_send(tenant_id, da_id, to_addresses))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    return {"message": "DA send initiated", "da_id": str(da_id)}
