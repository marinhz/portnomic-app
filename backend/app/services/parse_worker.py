"""Parse worker: orchestrates LLM call, validation, and persistence for a single email."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email
from app.models.emission_report import EmissionReport, FuelEntry
from app.models.parse_job import ParseJob
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.vessel import Vessel
from app.schemas.ai import ParsedEmailResult
from app.schemas.emission import EXTRACTION_SCHEMA_VERSION, EmissionExtractionResult
from app.services.carbon_price import get_current_price_eur
from app.services.emission_anomaly import detect_and_apply_anomalies
from app.services.emission_calculator import calculate_emissions, estimate_eua
from app.models.tenant_prompt_override import ParserType
from app.services.emission_parser import EMISSION_PROMPT_VERSION, parse_emission_content
from app.services.llm_client import LlmConfigError, is_transient_error, parse_email_content
from app.services.prompts import get_prompt
from app.services.report_type_detector import is_emission_report

logger = logging.getLogger("shipflow.parse_worker")


async def _resolve_vessel(
    db: AsyncSession, tenant_id: uuid.UUID, result: ParsedEmailResult
) -> uuid.UUID | None:
    """Find or create a vessel from parsed data."""
    if not result.vessel_name:
        return None

    if result.vessel_imo:
        stmt = select(Vessel).where(
            Vessel.tenant_id == tenant_id, Vessel.imo == result.vessel_imo
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing.id

    stmt = select(Vessel).where(
        Vessel.tenant_id == tenant_id, Vessel.name == result.vessel_name
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing.id

    vessel = Vessel(
        tenant_id=tenant_id,
        name=result.vessel_name,
        imo=result.vessel_imo,
    )
    db.add(vessel)
    await db.flush()
    return vessel.id


async def _resolve_port(
    db: AsyncSession, tenant_id: uuid.UUID, result: ParsedEmailResult
) -> uuid.UUID | None:
    """Find a port from parsed data."""
    if result.port_code:
        stmt = select(Port).where(
            ((Port.tenant_id == tenant_id) | (Port.tenant_id.is_(None))),
            Port.code == result.port_code,
        )
        port = (await db.execute(stmt)).scalar_one_or_none()
        if port:
            return port.id

    if result.port_name:
        stmt = select(Port).where(
            ((Port.tenant_id == tenant_id) | (Port.tenant_id.is_(None))),
            Port.name == result.port_name,
        )
        port = (await db.execute(stmt)).scalar_one_or_none()
        if port:
            return port.id

    return None


async def _create_or_update_port_call(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    vessel_id: uuid.UUID | None,
    port_id: uuid.UUID | None,
    result: ParsedEmailResult,
) -> uuid.UUID | None:
    """Create or update a port call from parsed data."""
    if not vessel_id or not port_id:
        return None

    eta = None
    etd = None
    if result.eta:
        try:
            eta = datetime.fromisoformat(result.eta)
        except ValueError:
            pass
    if result.etd:
        try:
            etd = datetime.fromisoformat(result.etd)
        except ValueError:
            pass

    port_call = PortCall(
        tenant_id=tenant_id,
        vessel_id=vessel_id,
        port_id=port_id,
        eta=eta,
        etd=etd,
        status="scheduled",
    )
    db.add(port_call)
    await db.flush()
    return port_call.id


async def _resolve_vessel_for_emission(
    db: AsyncSession, tenant_id: uuid.UUID, result: EmissionExtractionResult
) -> uuid.UUID | None:
    """Find or create a vessel from emission extraction data."""
    if not result.vessel_name:
        return None

    if result.imo_number and result.imo_number != "UNKNOWN":
        stmt = select(Vessel).where(
            Vessel.tenant_id == tenant_id, Vessel.imo == result.imo_number
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing.id

    stmt = select(Vessel).where(
        Vessel.tenant_id == tenant_id, Vessel.name == result.vessel_name
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing.id

    vessel = Vessel(
        tenant_id=tenant_id,
        name=result.vessel_name,
        imo=result.imo_number if result.imo_number != "UNKNOWN" else None,
    )
    db.add(vessel)
    await db.flush()
    return vessel.id


async def _persist_emission_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_id: uuid.UUID,
    result: EmissionExtractionResult,
    vessel_id: uuid.UUID,
    port_call_id: uuid.UUID | None,
) -> EmissionReport:
    """Create EmissionReport and FuelEntry records from extraction result."""
    report = EmissionReport(
        tenant_id=tenant_id,
        vessel_id=vessel_id,
        port_call_id=port_call_id,
        email_id=email_id,
        report_date=result.report_date,
        distance_nm=result.distance_nm,
        schema_version=EXTRACTION_SCHEMA_VERSION,
    )
    db.add(report)
    await db.flush()

    for fe in result.fuel_entries:
        entry = FuelEntry(
            emission_report_id=report.id,
            fuel_type=fe.fuel_type,
            consumption_mt=fe.consumption_mt,
            operational_status=fe.operational_status,
        )
        db.add(entry)
    await db.flush()
    return report


async def _process_emission_email(
    db: AsyncSession,
    email: Email,
    job: ParseJob,
    body: str,
) -> None:
    """Parse email as Noon/Bunker report and persist EmissionReport."""
    try:
        result = await parse_emission_content(
            body, email.subject, tenant_id=email.tenant_id, db=db
        )
    except LlmConfigError as exc:
        logger.warning("LLM config error for emission email %s: %s", email.id, exc)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        email.processing_status = "failed"
        email.error_reason = str(exc)
        email.prompt_version = EMISSION_PROMPT_VERSION
        await db.flush()
        return
    except Exception as exc:
        if is_transient_error(exc):
            raise
        logger.exception("LLM permanent failure for emission email %s", email.id)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        email.processing_status = "failed"
        email.error_reason = str(exc)
        email.prompt_version = EMISSION_PROMPT_VERSION
        email.retry_count += 1
        await db.flush()
        return

    vessel_id = await _resolve_vessel_for_emission(db, email.tenant_id, result)
    if not vessel_id:
        job.status = "failed"
        job.error_message = "Could not resolve vessel from emission extraction"
        job.completed_at = datetime.now(timezone.utc)
        email.processing_status = "failed"
        email.error_reason = "Could not resolve vessel"
        email.prompt_version = EMISSION_PROMPT_VERSION
        await db.flush()
        return

    emission_report = await _persist_emission_report(
        db,
        tenant_id=email.tenant_id,
        email_id=email.id,
        result=result,
        vessel_id=vessel_id,
        port_call_id=email.port_call_id,
    )
    await db.refresh(emission_report)  # Load fuel_entries for anomaly detection
    await detect_and_apply_anomalies(db, emission_report)

    result_dict = result.model_dump(mode="json")
    email.ai_raw_output = result_dict
    email.processing_status = "completed"
    email.prompt_version = EMISSION_PROMPT_VERSION
    email.error_reason = None

    carbon_price = await get_current_price_eur()
    emissions_result = calculate_emissions(result)
    eua_estimate = estimate_eua(result, carbon_price)

    job.status = "completed"
    job.result = {
        "type": "emission",
        "emission_report_id": str(emission_report.id),
        "extraction": result_dict,
        "emissions": emissions_result.model_dump(mode="json"),
        "eua_estimate": eua_estimate.model_dump(mode="json"),
        "anomaly_flags": emission_report.anomaly_flags,
        "status": emission_report.status,
    }
    job.prompt_version = EMISSION_PROMPT_VERSION
    job.completed_at = datetime.now(timezone.utc)

    await db.flush()
    logger.info(
        "Emission email %s parsed successfully, EmissionReport %s created, job %s completed",
        email.id,
        emission_report.id,
        job.id,
    )


async def process_email(
    db: AsyncSession,
    email_id: uuid.UUID,
    job_id: uuid.UUID,
    *,
    force_emission: bool = False,
) -> None:
    """Main worker entry point: load email, call LLM, validate, persist.

    Updates both the Email and ParseJob records.
    If force_emission or email is detected as Noon/Bunker report, uses emission parser.
    """
    email = (await db.execute(select(Email).where(Email.id == email_id))).scalar_one_or_none()
    if email is None:
        logger.error("Email %s not found, skipping", email_id)
        return

    if email.processing_status == "completed":
        logger.info("Email %s already completed, skipping (idempotent)", email_id)
        job = (await db.execute(select(ParseJob).where(ParseJob.id == job_id))).scalar_one_or_none()
        if job:
            job.status = "completed"
            job.result = email.ai_raw_output
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
        return

    job = (await db.execute(select(ParseJob).where(ParseJob.id == job_id))).scalar_one_or_none()
    if job is None:
        logger.error("ParseJob %s not found", job_id)
        return

    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    email.processing_status = "processing"
    await db.flush()

    body = email.body_text or email.body_html or ""
    if not body.strip():
        job.status = "failed"
        job.error_message = "Email has no body content"
        job.completed_at = datetime.now(timezone.utc)
        email.processing_status = "failed"
        email.error_reason = "Email has no body content"
        await db.flush()
        return

    use_emission_parser = force_emission or is_emission_report(
        email.subject, email.body_text, email.body_html
    )
    if use_emission_parser:
        await _process_emission_email(db, email, job, body)
        return

    prompt_text, prompt_version = await get_prompt(
        ParserType.DA_EMAIL.value, tenant_id=email.tenant_id, db=db
    )
    try:
        result = await parse_email_content(
            prompt_text, body, email.subject,
            tenant_id=email.tenant_id, db=db,
        )
    except LlmConfigError as exc:
        logger.warning("LLM config error for email %s: %s", email_id, exc)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        email.processing_status = "failed"
        email.error_reason = str(exc)
        email.prompt_version = prompt_version
        await db.flush()
        return
    except Exception as exc:
        if is_transient_error(exc):
            raise
        logger.exception("LLM permanent failure for email %s", email_id)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        email.processing_status = "failed"
        email.error_reason = str(exc)
        email.prompt_version = prompt_version
        email.retry_count += 1
        await db.flush()
        return

    result_dict = result.model_dump(mode="json")

    vessel_id = await _resolve_vessel(db, email.tenant_id, result)
    port_id = await _resolve_port(db, email.tenant_id, result)
    port_call_id = await _create_or_update_port_call(
        db, email.tenant_id, vessel_id, port_id, result
    )

    email.ai_raw_output = result_dict
    email.processing_status = "completed"
    email.prompt_version = prompt_version
    email.error_reason = None
    if port_call_id:
        email.port_call_id = port_call_id

    job.status = "completed"
    job.result = result_dict
    job.prompt_version = prompt_version
    job.completed_at = datetime.now(timezone.utc)

    await db.flush()
    logger.info("Email %s parsed successfully, job %s completed", email_id, job_id)
