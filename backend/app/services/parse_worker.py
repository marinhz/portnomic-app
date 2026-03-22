"""Parse worker: orchestrates LLM call, validation, and persistence for a single email."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.email import Email
from app.models.emission_report import EmissionReport, FuelEntry
from app.models.parse_job import ParseJob
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tenant_prompt_override import ParserType
from app.models.vessel import Vessel
from app.schemas.ai import ParsedEmailResult
from app.schemas.emission import EXTRACTION_SCHEMA_VERSION, EmissionExtractionResult
from app.services import audit as audit_svc
from app.services.carbon_price import get_current_price_eur
from app.services.disbursement_account import generate_da, upsert_da_from_parse
from app.services.emission_anomaly import detect_and_apply_anomalies
from app.services.emission_calculator import calculate_emissions, estimate_eua
from app.services.emission_parser import EMISSION_PROMPT_VERSION, parse_emission_content
from app.services.leakage_audit_trigger import trigger_leakage_audit_after_parse
from app.services.sentinel_audit_trigger import trigger_sentinel_audit_after_parse
from app.services.limits import check_da_limit
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
        stmt = select(Vessel).where(Vessel.tenant_id == tenant_id, Vessel.imo == result.vessel_imo)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing.id

    stmt = select(Vessel).where(Vessel.tenant_id == tenant_id, Vessel.name == result.vessel_name)
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
    """Find or create a port from parsed data."""
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

    # Port not found: create it so port call and DA can be created (e.g. Rotterdam for non-demo tenants).
    if result.port_code or result.port_name:
        name = result.port_name or result.port_code or "Unknown"
        code = result.port_code or (name[:20].upper().replace(" ", "") if name else "XX")
        port = Port(tenant_id=tenant_id, name=name, code=code)
        db.add(port)
        await db.flush()
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
        source="ai",
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
        stmt = select(Vessel).where(Vessel.tenant_id == tenant_id, Vessel.imo == result.imo_number)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing.id

    stmt = select(Vessel).where(Vessel.tenant_id == tenant_id, Vessel.name == result.vessel_name)
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


async def _find_existing_emission_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    vessel_id: uuid.UUID,
    report_date,
) -> EmissionReport | None:
    """Find existing Noon Report by unique key: vessel_id + report_date.

    One set of Noon Reports per vessel per date; additional uploads merge.
    """
    from datetime import date

    if isinstance(report_date, str):
        try:
            report_date = date.fromisoformat(report_date[:10])
        except (ValueError, TypeError):
            return None
    result = await db.execute(
        select(EmissionReport).where(
            EmissionReport.tenant_id == tenant_id,
            EmissionReport.vessel_id == vessel_id,
            EmissionReport.report_date == report_date,
        )
    )
    return result.scalar_one_or_none()


async def _persist_emission_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    result: EmissionExtractionResult,
    vessel_id: uuid.UUID,
    port_call_id: uuid.UUID | None,
    email_id: uuid.UUID | None = None,
    document_id: uuid.UUID | None = None,
) -> EmissionReport:
    """Create or merge EmissionReport. Unique key: vessel_id + report_date.

    - If no report exists: create new.
    - If exists: merge (update fuel entries) — one official version per date.
    Additional documents for same date update the report; Sentinel can compare
    via document ai_raw_output for audit.
    """
    existing = await _find_existing_emission_report(
        db, tenant_id, vessel_id, result.report_date
    )
    if existing:
        # Merge: replace fuel entries with new parsed data
        existing.fuel_entries.clear()
        for fe in result.fuel_entries:
            entry = FuelEntry(
                fuel_type=fe.fuel_type,
                consumption_mt=fe.consumption_mt,
                operational_status=fe.operational_status,
            )
            existing.fuel_entries.append(entry)
        existing.distance_nm = result.distance_nm
        if port_call_id is not None:
            existing.port_call_id = port_call_id
        await db.flush()
        await db.refresh(existing)
        logger.info(
            "Merged Noon Report %s for vessel %s date %s (duplicate upload)",
            existing.id,
            vessel_id,
            result.report_date,
        )
        return existing

    report = EmissionReport(
        tenant_id=tenant_id,
        vessel_id=vessel_id,
        port_call_id=port_call_id,
        email_id=email_id,
        document_id=document_id,
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
        result = await parse_emission_content(body, email.subject, tenant_id=email.tenant_id, db=db)
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
        result=result,
        vessel_id=vessel_id,
        port_call_id=email.port_call_id,
        email_id=email.id,
        document_id=None,
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

    # Sentinel audit trigger (Task 14.6): run for Noon Report documents
    if emission_report.port_call_id:
        try:
            await trigger_sentinel_audit_after_parse(
                db,
                email,
                emission_report.port_call_id,
                emission_report=emission_report,
            )
        except Exception as exc:
            logger.warning(
                "Sentinel audit failed for emission email %s (non-fatal): %s",
                email.id,
                exc,
                exc_info=True,
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
            prompt_text,
            body,
            email.subject,
            tenant_id=email.tenant_id,
            db=db,
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
    parsed_port_call_id = await _create_or_update_port_call(
        db, email.tenant_id, vessel_id, port_id, result
    )

    # Preserve manual-upload port_call_id; only overwrite when email had no association
    port_call_id = email.port_call_id if email.port_call_id else parsed_port_call_id
    if parsed_port_call_id and not email.port_call_id:
        await audit_svc.log_action(
            db,
            tenant_id=email.tenant_id,
            user_id=None,
            action="create",
            resource_type="port_call",
            resource_id=str(parsed_port_call_id),
            payload={"source": "ai"},
        )

    email.ai_raw_output = result_dict
    email.processing_status = "completed"
    email.prompt_version = prompt_version
    email.error_reason = None
    if parsed_port_call_id and not email.port_call_id:
        email.port_call_id = parsed_port_call_id

    job.status = "completed"
    job.result = result_dict
    job.prompt_version = prompt_version
    job.completed_at = datetime.now(timezone.utc)

    await db.flush()

    # Auto-create or update DA when we have a port call and parsed line items (disbursement email).
    da = None
    if port_call_id and result.line_items:
        da_type = "final" if (email.subject or "").lower().find("final") >= 0 else "proforma"
        da_limit = await check_da_limit(db, email.tenant_id)
        if da_limit.allowed:
            try:
                parsed_items = [
                    {
                        "description": li.description,
                        "amount": li.amount if li.amount is not None else 0.0,
                        "currency": li.currency or "USD",
                        "quantity": li.quantity or 1.0,
                        "unit_price": (
                            li.unit_price
                            if li.unit_price is not None
                            else (li.amount if li.amount is not None else 0.0)
                        ),
                    }
                    for li in result.line_items
                ]
                da, created = await upsert_da_from_parse(
                    db,
                    email.tenant_id,
                    port_call_id,
                    da_type,
                    parsed_items,
                    invoice_number=getattr(result, "invoice_number", None),
                )
                logger.info(
                    "%s DA %s from parsed email %s (type=%s)",
                    "Created" if created else "Updated",
                    da.id,
                    email_id,
                    da_type,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to auto-create/update DA from email %s: %s",
                    email_id,
                    exc,
                    exc_info=True,
                )
        else:
            logger.info(
                "DA limit exceeded for tenant %s (%d/%s), skipping auto-create from email %s",
                email.tenant_id,
                da_limit.current,
                da_limit.limit,
                email_id,
            )

        # Leakage audit trigger (Task 12.3): run for financial documents
        try:
            await trigger_leakage_audit_after_parse(db, email, da=da)
        except Exception as exc:
            logger.warning(
                "Leakage audit failed for email %s (non-fatal): %s",
                email_id,
                exc,
                exc_info=True,
            )

    # Sentinel audit trigger (Task 14.6): run for DA/SOF/Noon documents when we have port_call
    if port_call_id:
        try:
            await trigger_sentinel_audit_after_parse(
                db, email, port_call_id, da=da
            )
        except Exception as exc:
            logger.warning(
                "Sentinel audit failed for email %s (non-fatal): %s",
                email_id,
                exc,
                exc_info=True,
            )

    logger.info("Email %s parsed successfully, job %s completed", email_id, job_id)


async def _process_emission_document(
    db: AsyncSession,
    document: Document,
    job: ParseJob,
    body: str,
) -> None:
    """Parse document as Noon/Bunker report and persist EmissionReport."""
    try:
        result = await parse_emission_content(
            body, document.filename or "", tenant_id=document.tenant_id, db=db
        )
    except LlmConfigError as exc:
        logger.warning("LLM config error for emission document %s: %s", document.id, exc)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        document.processing_status = "failed"
        document.error_reason = str(exc)
        document.prompt_version = EMISSION_PROMPT_VERSION
        await db.flush()
        return
    except Exception as exc:
        if is_transient_error(exc):
            raise
        logger.exception("LLM permanent failure for emission document %s", document.id)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        document.processing_status = "failed"
        document.error_reason = str(exc)
        document.prompt_version = EMISSION_PROMPT_VERSION
        document.retry_count += 1
        await db.flush()
        return

    vessel_id = await _resolve_vessel_for_emission(db, document.tenant_id, result)
    if not vessel_id:
        job.status = "failed"
        job.error_message = "Could not resolve vessel from emission extraction"
        job.completed_at = datetime.now(timezone.utc)
        document.processing_status = "failed"
        document.error_reason = "Could not resolve vessel"
        document.prompt_version = EMISSION_PROMPT_VERSION
        await db.flush()
        return

    emission_report = await _persist_emission_report(
        db,
        tenant_id=document.tenant_id,
        result=result,
        vessel_id=vessel_id,
        port_call_id=document.port_call_id,
        email_id=None,
        document_id=document.id,
    )
    await db.refresh(emission_report)
    await detect_and_apply_anomalies(db, emission_report)

    result_dict = result.model_dump(mode="json")
    document.ai_raw_output = result_dict
    document.processing_status = "completed"
    document.prompt_version = EMISSION_PROMPT_VERSION
    document.error_reason = None

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
        "Emission document %s parsed successfully, EmissionReport %s created, job %s completed",
        document.id,
        emission_report.id,
        job.id,
    )

    if document.port_call_id:
        try:
            await trigger_sentinel_audit_after_parse(
                db,
                document,
                document.port_call_id,
                emission_report=emission_report,
            )
        except Exception as exc:
            logger.warning(
                "Sentinel audit failed for emission document %s (non-fatal): %s",
                document.id,
                exc,
                exc_info=True,
            )


async def process_document(
    db: AsyncSession,
    document_id: uuid.UUID,
    job_id: uuid.UUID,
    *,
    force_emission: bool = False,
) -> None:
    """Process a manually uploaded document: load document, call LLM, validate, persist.

    For MANUAL_UPLOAD: skips vessel/port resolution, uses document.port_call_id directly.
    Triggers DA auto-create, leakage audit, Sentinel same as email flow.
    """
    document = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if document is None:
        logger.error("Document %s not found, skipping", document_id)
        return

    if document.processing_status == "completed":
        logger.info("Document %s already completed, skipping (idempotent)", document_id)
        job = (await db.execute(select(ParseJob).where(ParseJob.id == job_id))).scalar_one_or_none()
        if job:
            job.status = "completed"
            job.result = document.ai_raw_output
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
        return

    job = (await db.execute(select(ParseJob).where(ParseJob.id == job_id))).scalar_one_or_none()
    if job is None:
        logger.error("ParseJob %s not found", job_id)
        return

    job.status = "processing"
    job.started_at = datetime.now(timezone.utc)
    document.processing_status = "processing"
    await db.flush()

    body = document.body_text or ""
    if not body.strip():
        job.status = "failed"
        job.error_message = "Document has no content"
        job.completed_at = datetime.now(timezone.utc)
        document.processing_status = "failed"
        document.error_reason = "Document has no content"
        await db.flush()
        return

    use_emission_parser = force_emission or (
        document.category == "noon_report"
        or is_emission_report(document.filename, document.body_text, None)
    )
    if use_emission_parser:
        await _process_emission_document(db, document, job, body)
        return

    prompt_text, prompt_version = await get_prompt(
        ParserType.DA_EMAIL.value, tenant_id=document.tenant_id, db=db
    )
    try:
        result = await parse_email_content(
            prompt_text,
            body,
            document.filename or "",
            tenant_id=document.tenant_id,
            db=db,
        )
    except LlmConfigError as exc:
        logger.warning("LLM config error for document %s: %s", document_id, exc)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        document.processing_status = "failed"
        document.error_reason = str(exc)
        document.prompt_version = prompt_version
        await db.flush()
        return
    except Exception as exc:
        if is_transient_error(exc):
            raise
        logger.exception("LLM permanent failure for document %s", document_id)
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        document.processing_status = "failed"
        document.error_reason = str(exc)
        document.prompt_version = prompt_version
        document.retry_count += 1
        await db.flush()
        return

    result_dict = result.model_dump(mode="json")
    port_call_id = document.port_call_id  # Always set for manual uploads

    document.ai_raw_output = result_dict
    document.processing_status = "completed"
    document.prompt_version = prompt_version
    document.error_reason = None

    job.status = "completed"
    job.result = result_dict
    job.prompt_version = prompt_version
    job.completed_at = datetime.now(timezone.utc)

    await db.flush()

    da = None
    if port_call_id and result.line_items:
        da_type = "final" if (document.filename or "").lower().find("final") >= 0 else "proforma"
        da_limit = await check_da_limit(db, document.tenant_id)
        if da_limit.allowed:
            try:
                parsed_items = [
                    {
                        "description": li.description,
                        "amount": li.amount if li.amount is not None else 0.0,
                        "currency": li.currency or "USD",
                        "quantity": li.quantity or 1.0,
                        "unit_price": (
                            li.unit_price
                            if li.unit_price is not None
                            else (li.amount if li.amount is not None else 0.0)
                        ),
                    }
                    for li in result.line_items
                ]
                da, created = await upsert_da_from_parse(
                    db,
                    document.tenant_id,
                    port_call_id,
                    da_type,
                    parsed_items,
                    invoice_number=getattr(result, "invoice_number", None),
                )
                logger.info(
                    "%s DA %s from parsed document %s (type=%s)",
                    "Created" if created else "Updated",
                    da.id,
                    document_id,
                    da_type,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to auto-create/update DA from document %s: %s",
                    document_id,
                    exc,
                    exc_info=True,
                )
        else:
            logger.info(
                "DA limit exceeded for tenant %s (%d/%s), skipping auto-create from document %s",
                document.tenant_id,
                da_limit.current,
                da_limit.limit,
                document_id,
            )

        try:
            await trigger_leakage_audit_after_parse(db, document, da=da)
        except Exception as exc:
            logger.warning(
                "Leakage audit failed for document %s (non-fatal): %s",
                document_id,
                exc,
                exc_info=True,
            )

    if port_call_id:
        try:
            await trigger_sentinel_audit_after_parse(db, document, port_call_id, da=da)
        except Exception as exc:
            logger.warning(
                "Sentinel audit failed for document %s (non-fatal): %s",
                document_id,
                exc,
                exc_info=True,
            )

    logger.info("Document %s parsed successfully, job %s completed", document_id, job_id)
