import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.tariff import TariffCreate, TariffResponse, TariffUpdate
from app.services import audit as audit_svc
from app.services import tariff as tariff_svc

router = APIRouter(prefix="/api/v1/tariffs", tags=["tariffs"])


@router.get(
    "",
    response_model=PaginatedResponse[TariffResponse],
)
async def list_tariffs(
    port_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
    current_user: CurrentUser = Depends(RequirePermission("da:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TariffResponse]:
    tariffs, total = await tariff_svc.list_tariffs(db, tenant_id, port_id, page, per_page)
    return PaginatedResponse(
        data=[TariffResponse.model_validate(t) for t in tariffs],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "",
    response_model=SingleResponse[TariffResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_tariff(
    body: TariffCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("da:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[TariffResponse]:
    tariff = await tariff_svc.create_tariff(db, tenant_id, body)
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="tariff",
        resource_id=str(tariff.id),
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=TariffResponse.model_validate(tariff))


@router.get(
    "/{tariff_id}",
    response_model=SingleResponse[TariffResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_tariff(
    tariff_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("da:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[TariffResponse]:
    tariff = await tariff_svc.get_tariff(db, tenant_id, tariff_id)
    if tariff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TARIFF_NOT_FOUND", "message": "Tariff not found"}},
        )
    return SingleResponse(data=TariffResponse.model_validate(tariff))


@router.put(
    "/{tariff_id}",
    response_model=SingleResponse[TariffResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_tariff(
    tariff_id: uuid.UUID,
    body: TariffUpdate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("da:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[TariffResponse]:
    tariff = await tariff_svc.update_tariff(db, tenant_id, tariff_id, body)
    if tariff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TARIFF_NOT_FOUND", "message": "Tariff not found"}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="tariff",
        resource_id=str(tariff.id),
        payload=body.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=TariffResponse.model_validate(tariff))
