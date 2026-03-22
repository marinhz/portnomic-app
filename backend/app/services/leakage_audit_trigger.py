"""Leakage audit trigger: runs after financial document parse, with idempotency and feature gating."""

from __future__ import annotations

import logging
from typing import Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.disbursement_account import DisbursementAccount
from app.models.document import Document
from app.models.email import Email
from app.models.port_call import PortCall
from app.services.audit_service import run_audit
from app.services.limits import PREMIUM_PLANS, get_tenant_plan

logger = logging.getLogger("shipflow.leakage_audit_trigger")

IDEMPOTENCY_KEY_PREFIX = "shipflow:leakage_audit:"
IDEMPOTENCY_TTL_SECONDS = 7 * 24 * 3600  # 7 days

ParsedEntity = Union[Email, Document]


def _is_financial_document(ai_raw_output: dict | None) -> bool:
    """Detect if ai_raw_output indicates a financial document (invoice) with line items."""
    if not ai_raw_output or not isinstance(ai_raw_output, dict):
        return False
    line_items = ai_raw_output.get("line_items") or []
    return len(line_items) > 0


async def trigger_leakage_audit_after_parse(
    db: AsyncSession,
    entity: ParsedEntity,
    *,
    da: DisbursementAccount | None = None,
) -> list | None:
    """Trigger leakage audit after parse job completes for a financial document.

    Supports both Email and Document (manual upload) sources.

    - Skips if not a financial document (no line_items in ai_raw_output).
    - Skips if idempotency key exists (same entity already audited).
    - Skips for Starter plans; only Professional/Enterprise.
    - Fetches PortCall and Vessel, invokes AuditService, persists anomalies.

    Returns list of created Anomaly records, or None if skipped.
    """
    if not _is_financial_document(entity.ai_raw_output):
        logger.debug("Entity %s has no line_items, skipping leakage audit", entity.id)
        return None

    from app.redis_client import redis_client

    idempotency_key = f"{IDEMPOTENCY_KEY_PREFIX}{entity.id}"
    if await redis_client.exists(idempotency_key):
        logger.info("Leakage audit already run for entity %s (idempotent), skipping", entity.id)
        return None

    plan = await get_tenant_plan(db, entity.tenant_id)
    if plan not in PREMIUM_PLANS:
        logger.debug(
            "Tenant %s on plan %s (Starter); skipping leakage audit for entity %s",
            entity.tenant_id,
            plan,
            entity.id,
        )
        return None

    port_call_id = entity.port_call_id
    if not port_call_id:
        logger.warning("Entity %s has no port_call_id, cannot run leakage audit", entity.id)
        return None

    stmt = (
        select(PortCall)
        .where(PortCall.id == port_call_id, PortCall.tenant_id == entity.tenant_id)
        .options(selectinload(PortCall.vessel))
    )
    result = await db.execute(stmt)
    port_call = result.scalar_one_or_none()
    if port_call is None:
        logger.warning("PortCall %s not found for entity %s", port_call_id, entity.id)
        return None

    vessel = port_call.vessel
    if vessel is None:
        logger.warning("PortCall %s has no vessel for entity %s", port_call_id, entity.id)
        return None

    try:
        anomalies = await run_audit(
            db,
            source=entity,
            port_call=port_call,
            vessel=vessel,
            da=da,
        )
    except Exception as exc:
        # Circuit breaker: LLM/network/audit failures do not block ingestion.
        # Mark as pending manual review; operator can override.
        failure_reason = f"{type(exc).__name__}: {exc}"
        logger.warning(
            "Leakage audit failed for entity %s (circuit breaker): %s",
            entity.id,
            failure_reason,
            exc_info=True,
        )
        entity.audit_status = "pending_manual_review"
        if da is not None:
            da.audit_status = "pending_manual_review"
        await db.flush()
        return None

    entity.audit_status = "completed"
    if da is not None:
        da.audit_status = "completed"
    await redis_client.set(idempotency_key, "1", ex=IDEMPOTENCY_TTL_SECONDS)
    logger.info(
        "Leakage audit for entity %s completed: %d anomalies",
        entity.id,
        len(anomalies),
    )
    return anomalies


__all__ = [
    "_is_financial_document",
    "trigger_leakage_audit_after_parse",
]
