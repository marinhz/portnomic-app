"""Sentinel audit trigger: runs after DA/SOF/Noon document parse, with idempotency and feature gating."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.disbursement_account import DisbursementAccount
from app.models.email import Email
from app.models.emission_report import EmissionReport
from app.services.limits import PREMIUM_PLANS, get_tenant_plan
from app.services.sentinel import AuditEngine

logger = logging.getLogger("shipflow.sentinel_audit_trigger")

IDEMPOTENCY_KEY_PREFIX = "shipflow:sentinel_audit:"
IDEMPOTENCY_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _has_da_data(ai_raw_output: dict | None) -> bool:
    """Detect if ai_raw_output indicates DA-relevant data (line items)."""
    if not ai_raw_output or not isinstance(ai_raw_output, dict):
        return False
    line_items = ai_raw_output.get("line_items") or []
    return len(line_items) > 0


def _has_sof_data(ai_raw_output: dict | None) -> bool:
    """Detect if ai_raw_output contains SOF timestamps or port log."""
    if not ai_raw_output or not isinstance(ai_raw_output, dict):
        return False
    sof_data = ai_raw_output.get("sof_timestamps") or ai_raw_output.get("port_log")
    return sof_data is not None and isinstance(sof_data, dict)


def _has_noon_data(emission_report: EmissionReport | None) -> bool:
    """Detect if we have Noon Report data from emission parse."""
    return emission_report is not None


def _is_relevant_for_sentinel(
    *,
    ai_raw_output: dict | None,
    da: DisbursementAccount | None,
    emission_report: EmissionReport | None,
) -> bool:
    """Return True if parsed data is relevant for Sentinel Triple-Check (DA, SOF, or Noon)."""
    return (
        _has_da_data(ai_raw_output)
        or (da is not None and (da.line_items or []))
        or _has_sof_data(ai_raw_output)
        or _has_noon_data(emission_report)
    )


async def trigger_sentinel_audit_after_parse(
    db: AsyncSession,
    email: Email,
    port_call_id: uuid.UUID,
    *,
    da: DisbursementAccount | None = None,
    emission_report: EmissionReport | None = None,
):
    """Trigger Sentinel audit after parse job completes for a relevant document.

    Trigger when new data affects one of: DA line items, SOF, Noon Report, or when
    port call has sufficient context for AIS lookup.

    - Skips if not a relevant document (no DA/SOF/Noon data).
    - Skips if idempotency key exists (same port_call + email already audited).
    - Skips for Starter plans; only Professional/Enterprise (align with Epic 12/8).
    - Invokes AuditEngine.compare_events, persists Discrepancy records.

    Non-blocking: Sentinel failure does not block core parse/ingest. Exceptions
    are caught and logged.

    Returns AuditReport if run, None if skipped.
    """
    if not _is_relevant_for_sentinel(
        ai_raw_output=email.ai_raw_output,
        da=da,
        emission_report=emission_report,
    ):
        logger.debug(
            "Email %s has no DA/SOF/Noon data relevant for Sentinel, skipping",
            email.id,
        )
        return None

    from app.redis_client import redis_client

    idempotency_key = f"{IDEMPOTENCY_KEY_PREFIX}{port_call_id}:{email.id}"
    if await redis_client.exists(idempotency_key):
        logger.info(
            "Sentinel audit already run for port_call %s + email %s (idempotent), skipping",
            port_call_id,
            email.id,
        )
        return None

    plan = await get_tenant_plan(db, email.tenant_id)
    if plan not in PREMIUM_PLANS:
        logger.debug(
            "Tenant %s on plan %s (Starter); skipping Sentinel audit for email %s",
            email.tenant_id,
            plan,
            email.id,
        )
        return None

    try:
        engine = AuditEngine(db, tenant_id=email.tenant_id)
        report = await engine.compare_events(port_call_id)
        await redis_client.set(idempotency_key, "1", ex=IDEMPOTENCY_TTL_SECONDS)
        logger.info(
            "Sentinel audit for port_call %s completed: %d discrepancies",
            port_call_id,
            report.total_count,
        )
        return report
    except Exception as exc:
        logger.warning(
            "Sentinel audit failed for port_call %s (non-fatal, parse not blocked): %s",
            port_call_id,
            exc,
            exc_info=True,
        )
        return None


__all__ = [
    "trigger_sentinel_audit_after_parse",
    "_is_relevant_for_sentinel",
    "_has_da_data",
    "_has_sof_data",
    "_has_noon_data",
]
