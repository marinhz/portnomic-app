"""Emissions API: Noon/Bunker report parsing and emission reports."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.models.emission_report import (
    REPORT_STATUS_FAILED,
    REPORT_STATUS_FLAGGED,
    REPORT_STATUS_VERIFIED,
)
from app.models.parse_job import ParseJob
from app.redis_client import redis_client
from app.schemas.ai import ParseJobResponse, ParseRequest
from app.schemas.auth import CurrentUser
from app.schemas.common import ErrorResponse, PaginatedResponse, PaginationMeta, SingleResponse
from app.schemas.emission import (
    EmissionReportDetailResponse,
    EmissionReportListResponse,
    EmissionReportOverride,
    EmissionReportResponse,
    EmissionsCalculateRequest,
    EmissionsCalculateResponse,
    EmissionsSummaryResponse,
)
from app.services import audit as audit_svc
from app.services import email_service, parse_job_service
from app.services import emission_export as emission_export_svc
from app.services import emission_report as emission_report_svc
from app.services.carbon_price import get_current_price_eur
from app.services.emission_calculator import calculate_emissions, estimate_eua
from app.services.limits import check_ai_parse_limit, raise_if_over_limit

router = APIRouter(prefix="/api/v1/emissions", tags=["emissions"])


def _status_to_compliance(report_status: str) -> str:
    """Map report status to compliance (green/yellow/red) for FuelEU display."""
    if report_status == REPORT_STATUS_VERIFIED:
        return "green"
    if report_status == REPORT_STATUS_FLAGGED:
        return "yellow"
    return "red"


def _status_to_verification(report_status: str) -> str:
    """Map report status to verification_status for frontend."""
    if report_status == REPORT_STATUS_VERIFIED:
        return "verified"
    if report_status == REPORT_STATUS_FLAGGED:
        return "flagged"
    if report_status == REPORT_STATUS_FAILED:
        return "flagged"
    return "pending"


@router.get(
    "/summary",
    response_model=SingleResponse[EmissionsSummaryResponse],
)
async def get_emissions_summary(
    vessel_id: uuid.UUID | None = Query(None, alias="vessel_id"),
    date_from: date | None = Query(None, alias="date_from"),
    date_to: date | None = Query(None, alias="date_to"),
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[EmissionsSummaryResponse]:
    """Aggregated carbon debt and compliance counts for dashboard."""
    reports, total = await emission_report_svc.list_emission_reports(
        db, tenant_id, page=1, per_page=10000, vessel_id=vessel_id, date_from=date_from, date_to=date_to
    )
    carbon_price = await get_current_price_eur()
    total_co2 = 0.0
    total_eua = 0.0
    compliance: dict[str, int] = {"green": 0, "yellow": 0, "red": 0}
    for r in reports:
        emissions = calculate_emissions(r)
        eua = estimate_eua(r, carbon_price)
        total_co2 += emissions.total_co2_mt
        total_eua += eua.cost_eur
        compliance[_status_to_compliance(r.status)] += 1
    return SingleResponse(
        data=EmissionsSummaryResponse(
            total_co2_mt=round(total_co2, 2),
            total_eua_estimate_eur=round(total_eua, 2) if total_eua else None,
            voyage_count=total,
            compliance=compliance,
        )
    )


@router.get(
    "/reports",
    response_model=PaginatedResponse[EmissionReportListResponse],
)
async def list_emission_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    vessel_id: uuid.UUID | None = Query(None, alias="vessel_id"),
    verification_status: str | None = Query(None, alias="verification_status"),
    date_from: date | None = Query(None, alias="date_from"),
    date_to: date | None = Query(None, alias="date_to"),
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[EmissionReportListResponse]:
    """List emission reports with optional filters."""
    reports, total = await emission_report_svc.list_emission_reports(
        db, tenant_id, page, per_page, vessel_id=vessel_id,
        verification_status=verification_status, date_from=date_from, date_to=date_to
    )
    carbon_price = await get_current_price_eur()
    items: list[EmissionReportListResponse] = []
    for r in reports:
        emissions = calculate_emissions(r)
        eua = estimate_eua(r, carbon_price)
        vessel_name = r.vessel.name if r.vessel else None
        items.append(
            EmissionReportListResponse(
                id=r.id,
                vessel_id=r.vessel_id,
                vessel_name=vessel_name,
                voyage_id=r.port_call_id,
                report_date=r.report_date,
                co2_mt=round(emissions.total_co2_mt, 2),
                eua_estimate_eur=round(eua.cost_eur, 2) if eua.cost_eur else None,
                compliance_status=_status_to_compliance(r.status),
                verification_status=_status_to_verification(r.status),
                source_email_id=r.email_id,
                created_at=r.created_at,
            )
        )
    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(total=total, page=page, per_page=per_page),
    )


@router.post(
    "/parse",
    response_model=SingleResponse[ParseJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        403: {"description": "Plan limit exceeded (upgrade_required)"},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def submit_emission_parse(
    body: ParseRequest,
    request: Request,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[ParseJobResponse]:
    """Submit an email for emission (Noon/Bunker report) parsing.

    Forces use of the emission extraction prompt and schema.
    Returns job id for polling status via GET /emissions/parse/{job_id}.
    """
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
        action="submit_emission_parse",
        resource_type="email",
        resource_id=str(em.id),
        payload={"job_id": str(job.id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Commit before pushing to Redis so the worker can find the job when it picks it up.
    await db.commit()

    await redis_client.rpush(
        "shipflow:parse_jobs",
        f"{job.id}:{em.id}:{tenant_id}:emission",
    )

    return SingleResponse(data=ParseJobResponse.model_validate(job))


@router.get(
    "/parse/{job_id}",
    response_model=SingleResponse[ParseJobResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_emission_parse_job(
    job_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[ParseJobResponse]:
    """Get status and result of an emission parse job."""
    job = await parse_job_service.get_parse_job(db, tenant_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "JOB_NOT_FOUND", "message": "Parse job not found"}},
        )
    return SingleResponse(data=ParseJobResponse.model_validate(job))


@router.get(
    "/reports/{report_id}",
    response_model=SingleResponse[EmissionReportDetailResponse],
    responses={404: {"model": ErrorResponse}},
)
async def get_emission_report(
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[EmissionReportDetailResponse]:
    """Get a single emission report by ID for dashboard.

    Includes co2_mt, eua_estimate, fuel_breakdown, anomaly_flags.
    """
    report = await emission_export_svc.get_report_for_export(db, tenant_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": "Emission report not found"}},
        )
    emissions = calculate_emissions(report)
    carbon_price = await get_current_price_eur()
    eua = estimate_eua(report, carbon_price)
    fuel_breakdown = [
        {"fuel_type": b.fuel_type, "consumption_mt": b.consumption_mt, "co2_mt": b.co2_mt}
        for b in emissions.per_fuel_breakdown
    ]
    anomaly_flags = []
    if report.anomaly_flags:
        for f in report.anomaly_flags:
            if isinstance(f, dict):
                anomaly_flags.append({
                    "code": f.get("rule", f.get("code", "unknown")),
                    "message": f.get("description", f.get("message", str(f))),
                })
    vessel = report.vessel
    return SingleResponse(
        data=EmissionReportDetailResponse(
            id=report.id,
            tenant_id=report.tenant_id,
            vessel_id=report.vessel_id,
            vessel_name=vessel.name if vessel else None,
            vessel_imo=str(vessel.imo) if vessel and vessel.imo else None,
            voyage_id=report.port_call_id,
            report_date=report.report_date,
            co2_mt=round(emissions.total_co2_mt, 2),
            eua_estimate_eur=round(eua.cost_eur, 2) if eua.cost_eur else None,
            compliance_status=_status_to_compliance(report.status),
            verification_status=_status_to_verification(report.status),
            fuel_breakdown=fuel_breakdown,
            anomaly_flags=anomaly_flags,
            source_email_id=report.email_id,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
    )


@router.get(
    "/reports/{report_id}/export",
    responses={
        400: {"description": "Invalid format"},
        404: {"model": ErrorResponse},
    },
)
async def export_emission_report(
    report_id: uuid.UUID,
    format: str = Query(..., alias="format", description="Export format: json, xml, or pdf"),
    voyage_id: uuid.UUID | None = Query(None, description="Optional voyage/port_call for aggregation"),
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate EU MRV compliant export in JSON, XML, or PDF.

    Suitable for direct submission or independent verifiers (DNV, Lloyd's Register).
    Includes vessel, period, fuel consumption, CO₂ emissions, distance, and source email reference.
    """
    fmt = format.lower().strip()
    if fmt not in ("json", "xml", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_FORMAT",
                    "message": "format must be json, xml, or pdf",
                }
            },
        )

    report = await emission_export_svc.get_report_for_export(db, tenant_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": "Emission report not found"}},
        )

    mrv_data = await emission_export_svc.build_mrv_data_for_export(report)

    if fmt == "json":
        content = emission_export_svc.export_json(mrv_data)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="eu-mrv-report.json"'},
        )
    if fmt == "xml":
        content = emission_export_svc.export_xml(mrv_data)
        return Response(
            content=content,
            media_type="application/xml",
            headers={"Content-Disposition": 'attachment; filename="eu-mrv-report.xml"'},
        )
    # pdf
    content, media_type = emission_export_svc.export_pdf(mrv_data)
    filename = "eu-mrv-report.pdf" if media_type == "application/pdf" else "eu-mrv-report.html"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch(
    "/reports/{report_id}",
    response_model=SingleResponse[EmissionReportResponse],
    responses={404: {"model": ErrorResponse}},
)
async def override_emission_report(
    report_id: uuid.UUID,
    body: EmissionReportOverride,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[EmissionReportResponse]:
    """Override anomaly flags after user review.

    Sets status to verified and clears anomaly_flags when override=true.
    """
    if not body.override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_REQUEST", "message": "override must be true"}},
        )
    report = await emission_report_svc.get_emission_report(db, tenant_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "REPORT_NOT_FOUND", "message": "Emission report not found"}},
        )
    report.status = REPORT_STATUS_VERIFIED
    report.anomaly_flags = None
    await db.flush()
    await db.refresh(report)
    return SingleResponse(data=EmissionReportResponse.model_validate(report))


@router.post(
    "/calculate",
    response_model=SingleResponse[EmissionsCalculateResponse],
)
async def calculate_emissions_endpoint(
    body: EmissionsCalculateRequest,
    current_user: CurrentUser = Depends(RequirePermission("ai:parse")),
) -> SingleResponse[EmissionsCalculateResponse]:
    """Calculate CO₂ emissions and EUA estimate from fuel entries.

    Uses formula E = C × f. Deterministic and auditable.
    Carbon price: uses live price from API/cache when not provided; fallback via FALLBACK_CARBON_PRICE_EUR.
    """
    carbon_price = body.carbon_price_eur
    if carbon_price is None:
        carbon_price = await get_current_price_eur()
    emissions = calculate_emissions(body)
    eua_estimate = estimate_eua(body, carbon_price)
    return SingleResponse(
        data=EmissionsCalculateResponse(
            emissions=emissions,
            eua_estimate=eua_estimate,
        )
    )
