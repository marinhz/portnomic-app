import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.email import EmailListResponse, EmailResponse, EmailUpdate
from app.services import audit as audit_svc
from app.services import email_service
from app.services import emission_report as emission_report_svc

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


@router.get("", response_model=PaginatedResponse[EmailListResponse])
async def list_emails(
    page: int = 1,
    per_page: int = 20,
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[EmailListResponse]:
    emails, total = await email_service.list_emails(
        db, tenant_id, page, per_page, status_filter=status_filter
    )
    return PaginatedResponse(
        data=[EmailListResponse.model_validate(e) for e in emails],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.get(
    "/{email_id}",
    response_model=SingleResponse[EmailResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_email(
    email_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[EmailResponse]:
    em = await email_service.get_email(db, tenant_id, email_id)
    if em is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EMAIL_NOT_FOUND", "message": "Email not found"}},
        )
    emission_report = await emission_report_svc.get_emission_report_by_email_id(
        db, tenant_id, em.id
    )
    data = EmailResponse.model_validate(em).model_dump()
    if emission_report:
        data["emission_report_id"] = emission_report.id
    return SingleResponse(data=EmailResponse(**data))


@router.patch(
    "/{email_id}",
    response_model=SingleResponse[EmailResponse],
    responses={404: {"model": ErrorResponse}},
)
async def update_email(
    email_id: uuid.UUID,
    body: EmailUpdate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[EmailResponse]:
    em = await email_service.get_email(db, tenant_id, email_id)
    if em is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EMAIL_NOT_FOUND", "message": "Email not found"}},
        )
    update_data = body.model_dump(exclude_unset=True)
    if "port_call_id" in update_data:
        em = await email_service.update_email_status(
            db, email_id, port_call_id=update_data["port_call_id"]
        )
        if em:
            await audit_svc.log_action(
                db,
                tenant_id=tenant_id,
                user_id=current_user.id,
                action="email_linked_to_port_call",
                resource_type="email",
                resource_id=str(email_id),
                payload={
                    "tenant_id": str(tenant_id),
                    "email_id": str(email_id),
                    "port_call_id": str(update_data["port_call_id"])
                    if update_data["port_call_id"]
                    else None,
                    "user_id": str(current_user.id),
                },
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
    emission_report = await emission_report_svc.get_emission_report_by_email_id(
        db, tenant_id, em.id
    )
    data = EmailResponse.model_validate(em).model_dump()
    if emission_report:
        data["emission_report_id"] = emission_report.id
    return SingleResponse(data=EmailResponse(**data))


@router.delete(
    "/{email_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def delete_email(
    email_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("admin:users")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    em = await email_service.get_email(db, tenant_id, email_id)
    if em is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EMAIL_NOT_FOUND", "message": "Email not found"}},
        )
    subject_truncated = (em.subject or "")[:100]
    for pj in em.parse_jobs:
        await db.delete(pj)
    await db.delete(em)
    await db.flush()
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="email_deleted",
        resource_type="email",
        resource_id=str(email_id),
        payload={
            "tenant_id": str(tenant_id),
            "email_id": str(email_id),
            "user_id": str(current_user.id),
            "subject_truncated": subject_truncated,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
