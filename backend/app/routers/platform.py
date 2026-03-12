import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.platform import get_platform_admin
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.services import audit as audit_svc
from app.services import tenant as tenant_svc

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


@router.post(
    "/tenants",
    response_model=SingleResponse[TenantResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_tenant(
    body: TenantCreate,
    request: Request,
    current_user: CurrentUser = Depends(get_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[TenantResponse]:
    try:
        tenant = await tenant_svc.create_tenant(
            db,
            name=body.name,
            slug=body.slug,
            plan=body.plan,
            settings=None,
            initial_admin_email=body.initial_admin_email,
            initial_admin_password=body.initial_admin_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_TENANT",
                    "message": str(e),
                }
            },
        )

    await audit_svc.log_action(
        db,
        tenant_id=tenant.id,
        user_id=current_user.id,
        action="create",
        resource_type="tenant",
        resource_id=str(tenant.id),
        payload={
            "name": body.name,
            "slug": body.slug,
            "plan": body.plan,
            "initial_admin_email": body.initial_admin_email,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    return SingleResponse(data=TenantResponse.model_validate(tenant))


@router.get(
    "/tenants",
    response_model=PaginatedResponse[TenantResponse],
)
async def list_tenants(
    page: int = 1,
    per_page: int = 20,
    current_user: CurrentUser = Depends(get_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TenantResponse]:
    tenants, total = await tenant_svc.list_tenants(db, page, per_page)
    return PaginatedResponse(
        data=[TenantResponse.model_validate(t) for t in tenants],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.get(
    "/tenants/{tenant_id}",
    response_model=SingleResponse[TenantResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_tenant(
    tenant_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[TenantResponse]:
    tenant = await tenant_svc.get_tenant(db, tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TENANT_NOT_FOUND",
                    "message": "Tenant not found",
                }
            },
        )
    return SingleResponse(data=TenantResponse.model_validate(tenant))


@router.patch(
    "/tenants/{tenant_id}",
    response_model=SingleResponse[TenantResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_tenant(
    tenant_id: uuid.UUID,
    body: TenantUpdate,
    request: Request,
    current_user: CurrentUser = Depends(get_platform_admin),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[TenantResponse]:
    tenant = await tenant_svc.update_tenant(db, tenant_id, body)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "TENANT_NOT_FOUND",
                    "message": "Tenant not found",
                }
            },
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="tenant",
        resource_id=str(tenant_id),
        payload=body.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return SingleResponse(data=TenantResponse.model_validate(tenant))
