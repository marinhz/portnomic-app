import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.vessel import VesselCreate, VesselResponse, VesselUpdate
from app.services import audit as audit_svc
from app.services import vessel as vessel_svc

router = APIRouter(prefix="/api/v1/vessels", tags=["vessels"])


@router.get(
    "",
    response_model=PaginatedResponse[VesselResponse],
)
async def list_vessels(
    page: int = 1,
    per_page: int = 20,
    current_user: CurrentUser = Depends(RequirePermission("vessel:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[VesselResponse]:
    vessels, total = await vessel_svc.list_vessels(db, tenant_id, page, per_page)
    return PaginatedResponse(
        data=[VesselResponse.model_validate(v) for v in vessels],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "",
    response_model=SingleResponse[VesselResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        403: {"description": "Plan limit exceeded (upgrade_required)"},
    },
)
async def create_vessel(
    body: VesselCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("vessel:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[VesselResponse]:
    vessel = await vessel_svc.create_vessel(db, tenant_id, body)
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="vessel",
        resource_id=str(vessel.id),
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=VesselResponse.model_validate(vessel))


@router.get(
    "/{vessel_id}",
    response_model=SingleResponse[VesselResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_vessel(
    vessel_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("vessel:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[VesselResponse]:
    vessel = await vessel_svc.get_vessel(db, tenant_id, vessel_id)
    if vessel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "VESSEL_NOT_FOUND", "message": "Vessel not found"}},
        )
    return SingleResponse(data=VesselResponse.model_validate(vessel))


@router.put(
    "/{vessel_id}",
    response_model=SingleResponse[VesselResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_vessel(
    vessel_id: uuid.UUID,
    body: VesselUpdate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("vessel:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[VesselResponse]:
    vessel = await vessel_svc.update_vessel(db, tenant_id, vessel_id, body)
    if vessel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "VESSEL_NOT_FOUND", "message": "Vessel not found"}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="vessel",
        resource_id=str(vessel.id),
        payload=body.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=VesselResponse.model_validate(vessel))
