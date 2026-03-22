import hashlib
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.models.document import Document
from app.models.parse_job import ParseJob
from app.redis_client import redis_client
from app.schemas.ai import ParseJobResponse
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.discrepancy import AuditReportResponse, DiscrepancyResponse, SourceLabelResponse
from app.schemas.port_call import (
    DocumentCategory,
    DocumentResponse,
    DocumentUploadResponse,
    PortCallCreate,
    PortCallResponse,
    PortCallUpdate,
)
from app.services import audit as audit_svc
from app.services import discrepancy as discrepancy_svc
from app.services.document_extraction import (
    extract_text_from_document,
    validate_file,
)
from app.services import document_service
from app.services.document_service import create_document, find_document_by_content_hash
from app.services.limits import check_ai_parse_limit, raise_if_over_limit
from app.services import parse_job_service
from app.services import port_call as port_call_svc
from app.services.sentinel import AuditEngine

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
    payload = {**body.model_dump(mode="json"), "source": body.source.value}
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="create",
        resource_type="port_call",
        resource_id=str(port_call.id),
        payload=payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=PortCallResponse.model_validate(port_call))


@router.post(
    "/{port_call_id}/audit",
    response_model=SingleResponse[AuditReportResponse],
    status_code=status.HTTP_200_OK,
    responses={404: {"model": ErrorResponse}},
)
async def run_sentinel_audit(
    port_call_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[AuditReportResponse]:
    """Run Sentinel Triple-Check audit on a port call."""
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    engine = AuditEngine(db, tenant_id)
    report = await engine.compare_events(port_call_id)
    return SingleResponse(
        data=AuditReportResponse(
            discrepancies=report.discrepancies,
            total_count=report.total_count,
            by_severity=report.by_severity,
            by_rule=report.by_rule,
            rules_executed=report.rules_executed,
        )
    )


@router.get(
    "/{port_call_id}/discrepancies",
    response_model=SingleResponse[list[DiscrepancyResponse]],
    responses={404: {"model": ErrorResponse}},
)
async def list_port_call_discrepancies(
    port_call_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[list[DiscrepancyResponse]]:
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    discrepancies = await discrepancy_svc.list_discrepancies_for_port_call(
        db, tenant_id, port_call_id
    )
    all_source_ids = [
        sid for d in discrepancies for sid in (d.source_documents or [])
    ]
    labels_map = await discrepancy_svc.resolve_source_labels(
        db, tenant_id, all_source_ids
    )
    enriched = []
    for d in discrepancies:
        resp = DiscrepancyResponse.model_validate(d)
        resp.source_labels = [
            SourceLabelResponse(id=sid, label=labels_map.get(sid, "Unknown source"))
            for sid in (d.source_documents or [])
        ]
        enriched.append(resp)
    return SingleResponse(data=enriched)


@router.delete(
    "/{port_call_id}/discrepancies",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_port_call_discrepancies(
    port_call_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("port_call:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete all Sentinel alerts (discrepancies) for a port call."""
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    await discrepancy_svc.delete_discrepancies_for_port_call(db, tenant_id, port_call_id)
    await db.commit()


async def _do_upload_document(
    port_call_id: uuid.UUID,
    request: Request,
    file: UploadFile,
    category: str,
    current_user: CurrentUser,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> SingleResponse[DocumentUploadResponse]:
    """Shared logic for document upload: creates Document (not Email), enqueues ParseJob."""
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )

    try:
        cat = DocumentCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_CATEGORY",
                    "message": "Category must be one of: sof, da, noon_report",
                }
            },
        ) from None

    data = await file.read()
    filename = file.filename or "document"
    content_type = file.content_type

    try:
        validate_file(filename, content_type, len(data))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_FILE", "message": str(e)}},
        ) from e

    # File fingerprinting: prevent redundant AI parsing and Sentinel audits
    content_hash = hashlib.sha256(data).hexdigest()
    existing = await find_document_by_content_hash(db, tenant_id, content_hash)
    if existing is not None:
        await db.commit()
        return SingleResponse(
            data=DocumentUploadResponse(
                job_id=None,  # No new job; document already processed
                document_id=existing.id,
                status="already_processed",
            )
        )

    try:
        extracted_text = extract_text_from_document(data, filename)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EXTRACTION_FAILED", "message": str(e)}},
        ) from e

    result = await check_ai_parse_limit(db, tenant_id)
    raise_if_over_limit(result, "ai_parse")

    doc = await create_document(
        db,
        tenant_id=tenant_id,
        port_call_id=port_call_id,
        filename=filename,
        body_text=extracted_text,
        category=cat.value,
        content_hash=content_hash,
    )

    job = ParseJob(
        tenant_id=tenant_id,
        document_id=doc.id,
        status="pending",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="manual_document_upload",
        resource_type="port_call",
        resource_id=str(port_call_id),
        payload={
            "document_id": str(doc.id),
            "job_id": str(job.id),
            "category": cat.value,
            "filename": filename,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    await db.commit()

    force_emission = cat == DocumentCategory.NOON_REPORT
    suffix = ":emission" if force_emission else ""
    await redis_client.rpush(
        "shipflow:parse_jobs",
        f"{job.id}:doc:{doc.id}:{tenant_id}{suffix}",
    )

    return SingleResponse(
        data=DocumentUploadResponse(job_id=job.id, document_id=doc.id, status="pending")
    )


@router.post(
    "/{port_call_id}/upload",
    response_model=SingleResponse[DocumentUploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        403: {"description": "Plan limit exceeded (upgrade_required)"},
        404: {"model": ErrorResponse},
    },
)
async def upload_port_call_document(
    port_call_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    category: str = Form(..., description="Document category: sof, da, noon_report"),
    current_user: CurrentUser = Depends(RequirePermission("port_call:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DocumentUploadResponse]:
    """Upload a document for manual Sentinel audit. Creates Document (not Email), triggers parse + Sentinel.

    Supported formats: PDF, XLSX, JPG (scanned invoices). Category: sof, da, noon_report.
    """
    return await _do_upload_document(
        port_call_id, request, file, category, current_user, tenant_id, db
    )


@router.post(
    "/{port_call_id}/documents",
    response_model=SingleResponse[DocumentUploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        403: {"description": "Plan limit exceeded (upgrade_required)"},
        404: {"model": ErrorResponse},
    },
    deprecated=True,
)
async def upload_port_call_document_deprecated(
    port_call_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    category: str = Form(..., description="Document category: sof, da, noon_report"),
    current_user: CurrentUser = Depends(RequirePermission("port_call:write")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[DocumentUploadResponse]:
    """Deprecated: Use POST /upload instead. Kept for backward compatibility."""
    return await _do_upload_document(
        port_call_id, request, file, category, current_user, tenant_id, db
    )


@router.get(
    "/{port_call_id}/documents",
    response_model=PaginatedResponse[DocumentResponse],
    responses={404: {"model": ErrorResponse}},
)
async def list_port_call_documents(
    port_call_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[DocumentResponse]:
    """List documents for a port call (manual uploads only; excludes emails)."""
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    docs, total = await document_service.list_documents(
        db, tenant_id, port_call_id, page, per_page, status_filter=status_filter
    )
    return PaginatedResponse(
        data=[DocumentResponse.model_validate(d) for d in docs],
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.get(
    "/{port_call_id}/documents/parse-status/{job_id}",
    response_model=SingleResponse[ParseJobResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_port_call_document_parse_status(
    port_call_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("port_call:read")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[ParseJobResponse]:
    """Get parse job status for a document uploaded to this port call."""
    port_call = await port_call_svc.get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    job = await parse_job_service.get_parse_job(db, tenant_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "JOB_NOT_FOUND", "message": "Parse job not found"}},
        )
    if job.document_id:
        doc_result = await db.execute(
            select(Document).where(
                Document.id == job.document_id,
                Document.tenant_id == tenant_id,
                Document.port_call_id == port_call_id,
            )
        )
        if doc_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "JOB_NOT_FOUND", "message": "Parse job not found"}},
            )
    else:
        from app.models.email import Email

        if not job.email_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "JOB_NOT_FOUND", "message": "Parse job not found"}},
            )
        em_result = await db.execute(
            select(Email).where(
                Email.id == job.email_id,
                Email.tenant_id == tenant_id,
                Email.port_call_id == port_call_id,
            )
        )
        if em_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "JOB_NOT_FOUND", "message": "Parse job not found"}},
            )
    return SingleResponse(data=ParseJobResponse.model_validate(job))


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
    port_call = await port_call_svc.update_port_call(db, tenant_id, port_call_id, body)
    if port_call is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PORT_CALL_NOT_FOUND", "message": "Port call not found"}},
        )
    payload = {**body.model_dump(exclude_unset=True, mode="json"), "source": port_call.source}
    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        action="update",
        resource_type="port_call",
        resource_id=str(port_call.id),
        payload=payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return SingleResponse(data=PortCallResponse.model_validate(port_call))
