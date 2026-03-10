import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.models.parse_job import ParseJob
from app.redis_client import redis_client
from app.schemas.ai import EmailStatusUpdate, ParseJobResponse, ParseRequest
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, SingleResponse
from app.services import audit as audit_svc
from app.services import email_service, parse_job_service
from app.services.limits import check_ai_parse_limit, raise_if_over_limit

logger = logging.getLogger("shipflow.ai")

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post(
    "/parse",
    response_model=SingleResponse[ParseJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={403: {"description": "Plan limit exceeded (upgrade_required)"}, 404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def submit_parse(
    body: ParseRequest,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[ParseJobResponse]:
    em = await email_service.get_email(db, tenant_id, body.email_id)
    if em is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EMAIL_NOT_FOUND", "message": "Email not found"}},
        )

    if em.processing_status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "ALREADY_PROCESSING",
                    "message": "Email is already being processed",
                }
            },
        )

    result = await check_ai_parse_limit(db, tenant_id)
    raise_if_over_limit(result, "ai_parse")

    job = ParseJob(
        tenant_id=tenant_id,
        email_id=em.id,
        status="pending",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    em.processing_status = "pending"
    em.error_reason = None
    await db.flush()

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="submit_parse",
        resource_type="email",
        resource_id=str(em.id),
        payload={"job_id": str(job.id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Commit before pushing to Redis so the worker can find the job when it picks it up.
    # Without this, a race occurs: worker blpop gets the job before API commits, worker
    # loads ParseJob by id, gets None, logs and returns; job is lost from queue.
    await db.commit()

    await redis_client.rpush(
        "shipflow:parse_jobs",
        f"{job.id}:{em.id}:{tenant_id}",
    )
    logger.info(
        "Parse job enqueued job_id=%s email_id=%s tenant_id=%s",
        job.id, em.id, tenant_id,
    )

    return SingleResponse(data=ParseJobResponse.model_validate(job))


@router.get(
    "/parse/{job_id}",
    response_model=SingleResponse[ParseJobResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_parse_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[ParseJobResponse]:
    job = await parse_job_service.get_parse_job(db, tenant_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "JOB_NOT_FOUND", "message": "Parse job not found"}},
        )
    return SingleResponse(data=ParseJobResponse.model_validate(job))


@router.put(
    "/emails/{email_id}/status",
    response_model=SingleResponse[dict],
    responses={404: {"model": ErrorResponse}},
)
async def update_email_status(
    email_id: uuid.UUID,
    body: EmailStatusUpdate,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[dict]:
    """Manual override: mark email as invalid/skip or reset for re-processing."""
    em = await email_service.get_email(db, tenant_id, email_id)
    if em is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EMAIL_NOT_FOUND", "message": "Email not found"}},
        )

    if body.processing_status:
        em.processing_status = body.processing_status
    if body.error_reason is not None:
        em.error_reason = body.error_reason
    await db.flush()

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update_email_status",
        resource_type="email",
        resource_id=str(em.id),
        payload=body.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return SingleResponse(data={"status": em.processing_status})
