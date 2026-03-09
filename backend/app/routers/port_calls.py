import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.port_call import PortCallCreate, PortCallResponse, PortCallUpdate
from app.services import audit as audit_svc
from app.services import port_call as port_call_svc

router = APIRouter(prefix="/api/v1/port-calls", tags=["port-calls"])


@router.get(
    "",
    response_model=PaginatedResponse[PortCallResponse],
)
async def list_port_calls(
    page: int = 1,
    per_page: int = 20,
    vessel_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PortCallResponse]:
    port_calls, total = await port_call_svc.list_port_calls(
        db, tenant_id, page, per_page, vessel_id=vessel_id, status=status_filter
    )
    return PaginatedResponse(
        data=[PortCallResponse.model_validate(pc) for pc in port_calls],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "",
    response_model=SingleResponse[PortCallResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_port_call(
    body: PortCallCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("port_call:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[PortCallResponse]:
    port_call = await port_call_svc.create_port_call(db, tenant_id, body)
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="port_call",
        resource_id=str(port_call.id),
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=PortCallResponse.model_validate(port_call))


@router.get(
    "/{port_call_id}",
    response_model=SingleResponse[PortCallResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_port_call(
    port_call_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[PortCallResponse]:
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    return SingleResponse(data=PortCallResponse.model_validate(port_call))


@router.put(
    "/{port_call_id}",
    response_model=SingleResponse[PortCallResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_port_call(
    port_call_id: uuid.UUID,
    body: PortCallUpdate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("port_call:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[PortCallResponse]:
    port_call = await port_call_svc.update_port_call(
        db, tenant_id, port_call_id, body
    )
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="port_call",
        resource_id=str(port_call.id),
        payload=body.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=PortCallResponse.model_validate(port_call))
