import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.permissions_manifest import PERMISSIONS_MANIFEST
from app.schemas.admin import (
    PermissionsManifest,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.services import admin as admin_svc
from app.services import audit as audit_svc

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ── Users ────────────────────────────────────────────────────────────────────


@router.get(
    "/users",
    response_model=PaginatedResponse[UserResponse],
)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    users, total = await admin_svc.list_users(db, tenant_id, page, per_page)
    return PaginatedResponse(
        data=[UserResponse.model_validate(u) for u in users],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "/users",
    response_model=SingleResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        403: {"description": "Plan limit exceeded (upgrade_required)"},
    },
)
async def create_user(
    body: UserCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[UserResponse]:
    user = await admin_svc.create_user(db, tenant_id, body)
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="user",
        resource_id=str(user.id),
        payload={"email": body.email, "role_id": str(body.role_id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=UserResponse.model_validate(user))


@router.get(
    "/users/{user_id}",
    response_model=SingleResponse[UserResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[UserResponse]:
    user = await admin_svc.get_user(db, tenant_id, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    return SingleResponse(data=UserResponse.model_validate(user))


@router.put(
    "/users/{user_id}",
    response_model=SingleResponse[UserResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[UserResponse]:
    user = await admin_svc.update_user(db, tenant_id, user_id, body)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=str(user.id),
        payload=body.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=UserResponse.model_validate(user))


# ── Permissions manifest ──────────────────────────────────────────────────────


@router.get(
    "/permissions",
    response_model=SingleResponse[PermissionsManifest],
)
async def get_permissions_manifest(
    current_user: CurrentUser = Depends(RequirePermission("admin:roles")),
) -> SingleResponse[PermissionsManifest]:
    """Return the full permissions manifest grouped by module."""
    return SingleResponse(data=PermissionsManifest(modules=PERMISSIONS_MANIFEST))


# ── Roles ────────────────────────────────────────────────────────────────────


@router.get(
    "/roles",
    response_model=SingleResponse[list[RoleResponse]],
)
async def list_roles(
    current_user: CurrentUser = Depends(RequirePermission("admin:roles")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[list[RoleResponse]]:
    roles = await admin_svc.list_roles(db, tenant_id)
    return SingleResponse(data=[RoleResponse.model_validate(r) for r in roles])


@router.get(
    "/roles/{role_id}",
    response_model=SingleResponse[RoleResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_role(
    role_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("admin:roles")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[RoleResponse]:
    role = await admin_svc.get_role(db, tenant_id, role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ROLE_NOT_FOUND", "message": "Role not found"}},
        )
    return SingleResponse(data=RoleResponse.model_validate(role))


@router.post(
    "/roles",
    response_model=SingleResponse[RoleResponse],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def create_role(
    body: RoleCreate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:roles")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[RoleResponse]:
    role = await admin_svc.create_role(db, tenant_id, body)
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="role",
        resource_id=str(role.id),
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=RoleResponse.model_validate(role))


@router.put(
    "/roles/{role_id}",
    response_model=SingleResponse[RoleResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_role(
    role_id: uuid.UUID,
    body: RoleUpdate,
    request: Request,
    current_user: CurrentUser = Depends(
        RequirePermission("admin:roles", allow_platform_admin=True)
    ),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[RoleResponse]:
    # Platform admins can grant any permission; others are restricted to permissions they have
    actor_perms = None if current_user.is_platform_admin else current_user.permissions
    try:
        role = await admin_svc.update_role(
            db, tenant_id, role_id, body, actor_permissions=actor_perms
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "PRIVILEGE_ESCALATION", "message": str(e)}},
        )
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ROLE_NOT_FOUND", "message": "Role not found"}},
        )
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="role",
        resource_id=str(role.id),
        payload=body.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=RoleResponse.model_validate(role))
