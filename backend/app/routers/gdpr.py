import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, SingleResponse
from app.schemas.gdpr import (
    DataExportRequest,
    DataExportResponse,
    ErasureRequest,
    ErasureResponse,
    ProcessingRecordEntry,
    RetentionPolicyConfig,
    RetentionPolicyResponse,
)

_EXPORT_FORMAT_VALUES = ("json", "csv")
from app.services import audit as audit_svc
from app.services import gdpr as gdpr_svc

router = APIRouter(prefix="/api/v1/gdpr", tags=["gdpr"])


# ── Data Export ──────────────────────────────────────────────────────────────


@router.post(
    "/export",
    response_model=SingleResponse[DataExportResponse],
    responses={400: {"model": ErrorResponse}},
)
async def export_own_data(
    body: DataExportRequest,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("*")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DataExportResponse]:
    if body.format not in _EXPORT_FORMAT_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "INVALID_FORMAT", "message": "Format must be 'json' or 'csv'"}
            },
        )

    export_data = await gdpr_svc.export_user_data(db, tenant_id, current_user.id, body.format)
    if "error" in export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    export_id = str(uuid.uuid4())

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="gdpr_export",
        resource_type="user",
        resource_id=str(current_user.id),
        payload={"format": body.format, "export_id": export_id},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SingleResponse(
        data=DataExportResponse(
            export_id=export_id,
            status="ready",
            data=export_data,
            created_at=datetime.now(timezone.utc),
        )
    )


@router.post(
    "/export/{user_id}",
    response_model=SingleResponse[DataExportResponse],
    responses={404: {"model": ErrorResponse}},
)
async def export_user_data(
    user_id: uuid.UUID,
    body: DataExportRequest,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DataExportResponse]:
    if body.format not in _EXPORT_FORMAT_VALUES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "INVALID_FORMAT", "message": "Format must be 'json' or 'csv'"}
            },
        )

    export_data = await gdpr_svc.export_user_data(db, tenant_id, user_id, body.format)
    if "error" in export_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    export_id = str(uuid.uuid4())

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="gdpr_export",
        resource_type="user",
        resource_id=str(user_id),
        payload={"format": body.format, "export_id": export_id, "target_user_id": str(user_id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SingleResponse(
        data=DataExportResponse(
            export_id=export_id,
            status="ready",
            data=export_data,
            created_at=datetime.now(timezone.utc),
        )
    )


# ── Right to Erasure ────────────────────────────────────────────────────────


@router.post(
    "/erasure",
    response_model=SingleResponse[ErasureResponse],
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def request_erasure(
    body: ErasureRequest,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[ErasureResponse]:
    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "CONFIRMATION_REQUIRED",
                    "message": "Set confirm=true to proceed with erasure",
                }
            },
        )

    result = await gdpr_svc.erase_user(db, tenant_id, body.user_id, current_user.id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="gdpr_erasure_request",
        resource_type="user",
        resource_id=str(body.user_id),
        payload={"reason": body.reason},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SingleResponse(
        data=ErasureResponse(
            user_id=result["user_id"],
            status=result["status"],
            anonymized_fields=result["anonymized_fields"],
            retained_for_legal=result["retained_for_legal"],
            processed_at=result["processed_at"],
        )
    )


# ── Retention Policy ────────────────────────────────────────────────────────


@router.get(
    "/retention",
    response_model=SingleResponse[RetentionPolicyResponse],
)
async def get_retention_policy(
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[RetentionPolicyResponse]:
    result = await gdpr_svc.get_retention_policy(db, tenant_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}},
        )

    return SingleResponse(
        data=RetentionPolicyResponse(
            tenant_id=result["tenant_id"],
            config=RetentionPolicyConfig(**result["config"]),
            updated_at=result.get("updated_at"),
        )
    )


@router.put(
    "/retention",
    response_model=SingleResponse[RetentionPolicyResponse],
    responses={400: {"model": ErrorResponse}},
)
async def update_retention_policy(
    body: RetentionPolicyConfig,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[RetentionPolicyResponse]:
    result = await gdpr_svc.update_retention_policy(db, tenant_id, body.model_dump())
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TENANT_NOT_FOUND", "message": "Tenant not found"}},
        )

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="retention_policy",
        payload=body.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SingleResponse(
        data=RetentionPolicyResponse(
            tenant_id=result["tenant_id"],
            config=RetentionPolicyConfig(**result["config"]),
            updated_at=result.get("updated_at"),
        )
    )


# ── Processing Records (GDPR Article 30) ───────────────────────────────────


@router.get(
    "/processing-records",
    response_model=SingleResponse[list[ProcessingRecordEntry]],
)
async def get_processing_records(
    current_user: CurrentUser = Depends(RequirePermission("*")),
) -> SingleResponse[list[ProcessingRecordEntry]]:
    records = gdpr_svc.get_processing_records()
    return SingleResponse(data=records)
