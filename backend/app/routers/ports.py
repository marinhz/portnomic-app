import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.port import PortCreate, PortResponse
from app.services import audit as audit_svc
from app.services import port as port_svc

router = APIRouter(prefix="/api/v1/ports", tags=["ports"])


@router.get("", response_model=PaginatedResponse[PortResponse])
async def list_ports(
    page: int = 1,
    per_page: int = 20,
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[PortResponse]:
    ports, total = await port_svc.list_ports(db, tenant_id, page, per_page)
    return PaginatedResponse(
        data=[PortResponse.model_validate(p) for p in ports],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "",
    response_model=SingleResponse[PortResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_port(
    body: PortCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("port_call:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[PortResponse]:
    port = await port_svc.create_port(db, tenant_id, body)
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="port",
        resource_id=str(port.id),
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=PortResponse.model_validate(port))


@router.get(
    "/{port_id}",
    response_model=SingleResponse[PortResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_port(
    port_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[PortResponse]:
    port = await port_svc.get_port(db, tenant_id, port_id)
    if port is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_NOT_FOUND", "message": "Port not found"}},
        )
    return SingleResponse(data=PortResponse.model_validate(port))
