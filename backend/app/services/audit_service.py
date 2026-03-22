"""AuditService for AI Leakage Detector — applies LD-001 through LD-004 and persists anomalies."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Union

from app.models.anomaly import ANOMALY_RULE_IDS, Anomaly
from app.models.disbursement_account import DisbursementAccount
from app.models.document import Document
from app.models.email import Email
from app.models.emission_report import EmissionReport
from app.models.port_call import PortCall
from app.models.vessel import Vessel
from app.services.audit import log_action

logger = logging.getLogger("shipflow.audit_service")

# Rule severity mapping
RULE_SEVERITY: dict[str, str] = {
    "LD-001": "high",
    "LD-002": "medium",
    "LD-003": "medium",
    "LD-004": "high",
}


def _parse_service_date(value: str | None) -> datetime | None:
    """Parse ISO 8601 date/time string; return None if invalid."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _is_weekend_or_holiday(dt: datetime) -> bool:
    """Check if date falls on weekend (Sat/Sun). Holiday check is simplified for MVP."""
    return dt.weekday() >= 5


def _make_ld001_anomaly(
    li: dict[str, Any],
    service_date: datetime,
    eta: datetime | None,
    etd: datetime | None,
    before_arrival: bool,
) -> dict[str, Any]:
    """Build LD-001 anomaly dict for temporal validation."""
    desc = li.get("description", "Line item")[:100]
    amount = li.get("amount")
    if amount is not None:
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            amount = None
    if before_arrival:
        desc_text = (
            f"Service date {service_date.isoformat()} is before vessel ETA "
            f"{eta.isoformat()}. Service cannot have occurred before arrival."
        )
    else:
        desc_text = (
            f"Service date {service_date.isoformat()} is after vessel ETD "
            f"{etd.isoformat()}. Service cannot have occurred after departure."
        )
    return {
        "rule_id": "LD-001",
        "severity": RULE_SEVERITY["LD-001"],
        "line_item_ref": desc,
        "invoiced_value": amount,
        "expected_value": None,
        "description": desc_text,
        "raw_evidence": {
            "service_date": li.get("service_date"),
            "eta": eta.isoformat() if eta else None,
            "etd": etd.isoformat() if etd else None,
        },
    }


def _ld001_temporal_validation(
    line_items: list[dict[str, Any]],
    eta: datetime | None,
    etd: datetime | None,
) -> list[dict[str, Any]]:
    """LD-001: Invoice service date must fall within vessel stay (eta/etd)."""
    anomalies: list[dict[str, Any]] = []
    if not eta and not etd:
        return anomalies

    for li in line_items:
        service_date = _parse_service_date(li.get("service_date"))
        if service_date is None:
            continue
        if eta and service_date < eta:
            anomalies.append(_make_ld001_anomaly(li, service_date, eta, etd, True))
        elif etd and service_date > etd:
            anomalies.append(_make_ld001_anomaly(li, service_date, eta, etd, False))

    return anomalies


def _ld002_duplicate_detection(
    all_line_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """LD-002: Identical service/amount in same PortCall (duplicate)."""
    anomalies: list[dict[str, Any]] = []
    seen: dict[tuple[str, float], dict[str, Any]] = {}

    for li in all_line_items:
        desc = (li.get("description") or "").strip()
        amt = li.get("amount")
        if amt is not None:
            try:
                amt = float(amt)
            except (ValueError, TypeError):
                continue
            key = (desc, amt)
            if key in seen:
                anomalies.append(
                    {
                        "rule_id": "LD-002",
                        "severity": RULE_SEVERITY["LD-002"],
                        "line_item_ref": desc[:512],
                        "invoiced_value": Decimal(str(amt)),
                        "expected_value": None,
                        "description": (
                            f"Duplicate line item: '{desc}' for {amt} already exists "
                            "in this port call."
                        ),
                        "raw_evidence": {"description": desc, "amount": amt},
                    }
                )
            else:
                seen[key] = li

    return anomalies


def _make_ld003_anomaly(li: dict[str, Any], service_date: datetime) -> dict[str, Any]:
    """Build LD-003 anomaly for tariff shift (weekend rate on weekday)."""
    amount = li.get("amount")
    if amount is not None:
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            amount = None
    return {
        "rule_id": "LD-003",
        "severity": RULE_SEVERITY["LD-003"],
        "line_item_ref": (li.get("description") or "Line item")[:100],
        "invoiced_value": amount,
        "expected_value": None,
        "description": (
            f"Line item mentions Weekend/Holiday rate but service date "
            f"{service_date.date()} is a weekday. Standard hours rate may apply."
        ),
        "raw_evidence": {
            "service_date": li.get("service_date"),
            "description": li.get("description"),
        },
    }


def _ld003_tariff_shift(
    line_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """LD-003: 'Weekend/Holiday' rate when service was during standard hours."""
    anomalies: list[dict[str, Any]] = []
    weekend_keywords = ("weekend", "holiday", "out of hours", "overtime")

    for li in line_items:
        desc = (li.get("description") or "").lower()
        if not any(kw in desc for kw in weekend_keywords):
            continue
        service_date = _parse_service_date(li.get("service_date"))
        if service_date is None:
            continue
        if not _is_weekend_or_holiday(service_date):
            anomalies.append(_make_ld003_anomaly(li, service_date))

    return anomalies


def _ld004_quantity_variance(
    line_items: list[dict[str, Any]],
    emission_reports: list[EmissionReport],
    vessel: Vessel | None = None,
) -> list[dict[str, Any]]:
    """LD-004: Invoiced tug/pilot hours vs Noon Reports.

    Simplified: flag tug/pilot services with quantity > 24h per port call as suspicious,
    or when Noon Report data exists but cannot be reconciled (placeholder for future).
    """
    anomalies: list[dict[str, Any]] = []
    tug_pilot_keywords = ("tug", "pilot", "pilotage")

    total_invoiced_hours = 0.0
    for li in line_items:
        desc = (li.get("description") or "").lower()
        if not any(kw in desc for kw in tug_pilot_keywords):
            continue
        qty = li.get("quantity")
        if qty is not None:
            try:
                total_invoiced_hours += float(qty)
            except (ValueError, TypeError):
                pass

    # Heuristic: > 24h tug/pilot for single port call is suspicious
    if total_invoiced_hours > 24.0:
        anomalies.append(
            {
                "rule_id": "LD-004",
                "severity": RULE_SEVERITY["LD-004"],
                "line_item_ref": f"Tug/Pilot services (total {total_invoiced_hours}h)",
                "invoiced_value": Decimal(str(total_invoiced_hours)),
                "expected_value": None,
                "description": (
                    f"Invoiced tug/pilot hours ({total_invoiced_hours}) exceed 24h for "
                    "single port call. Verify against Noon Reports."
                ),
                "raw_evidence": {
                    "total_invoiced_hours": total_invoiced_hours,
                    "noon_reports_count": len(emission_reports),
                    "vessel_id": str(vessel.id) if vessel else None,
                },
            }
        )

    return anomalies


async def run_audit(
    db: AsyncSession,
    *,
    source: Union[Email, Document],
    port_call: PortCall,
    vessel: Vessel,  # Reserved for LD-004 vessel-dimension checks
    da: DisbursementAccount | None = None,
) -> list[Anomaly]:
    """Run leakage audit (LD-001 through LD-004) and persist anomalies.

    Input: Email or Document (with ai_raw_output), PortCall, Vessel, optional DA.
    Output: List of persisted Anomaly records.
    """
    tenant_id = source.tenant_id
    ai_raw = source.ai_raw_output or {}
    line_items = ai_raw.get("line_items") or []

    if not line_items:
        logger.debug("No line items in ai_raw_output for source %s, skipping audit", source.id)
        return []

    email_id = source.id if isinstance(source, Email) else None
    document_id = source.id if isinstance(source, Document) else None

    # Collect existing DA line items for this port call (for LD-002)
    stmt = select(DisbursementAccount).where(
        DisbursementAccount.tenant_id == tenant_id,
        DisbursementAccount.port_call_id == port_call.id,
    )
    result = await db.execute(stmt)
    das = list(result.scalars().all())

    all_line_items_for_ld002: list[dict[str, Any]] = []
    for d in das:
        for li in d.line_items or []:
            all_line_items_for_ld002.append(
                {
                    "description": li.get("description"),
                    "amount": li.get("amount"),
                }
            )
    for li in line_items:
        all_line_items_for_ld002.append(
            {
                "description": li.get("description"),
                "amount": li.get("amount"),
            }
        )

    # Emission reports for port call (LD-004)
    stmt = select(EmissionReport).where(
        EmissionReport.tenant_id == tenant_id,
        EmissionReport.port_call_id == port_call.id,
    )
    er_result = await db.execute(stmt)
    emission_reports = list(er_result.scalars().all())

    # Run detection rules
    anomalies_data: list[dict[str, Any]] = []

    anomalies_data.extend(
        _ld001_temporal_validation(
            line_items,
            port_call.eta,
            port_call.etd,
        )
    )
    anomalies_data.extend(_ld002_duplicate_detection(all_line_items_for_ld002))
    anomalies_data.extend(_ld003_tariff_shift(line_items))
    anomalies_data.extend(_ld004_quantity_variance(line_items, emission_reports, vessel))

    # Persist anomalies and log to AuditLog
    created: list[Anomaly] = []
    for a in anomalies_data:
        anomaly = Anomaly(
            tenant_id=tenant_id,
            email_id=email_id,
            document_id=document_id,
            da_id=da.id if da else None,
            port_call_id=port_call.id,
            rule_id=a["rule_id"],
            severity=a["severity"],
            line_item_ref=a.get("line_item_ref"),
            invoiced_value=a.get("invoiced_value"),
            expected_value=a.get("expected_value"),
            description=a["description"],
            raw_evidence=a.get("raw_evidence"),
        )
        db.add(anomaly)
        await db.flush()
        created.append(anomaly)

        await log_action(
            db,
            tenant_id=tenant_id,
            user_id=None,
            action="leakage_audit_rule",
            resource_type="anomaly",
            resource_id=str(anomaly.id),
            payload={
                "rule_id": a["rule_id"],
                "result": "fail",
                "source_id": str(source.id),
                "port_call_id": str(port_call.id),
            },
        )

    # Log pass for rules that did not flag
    for rule_id in ANOMALY_RULE_IDS:
        if not any(a["rule_id"] == rule_id for a in anomalies_data):
            await log_action(
                db,
                tenant_id=tenant_id,
                user_id=None,
                action="leakage_audit_rule",
                resource_type="document" if document_id else "email",
                resource_id=str(source.id),
                payload={
                    "rule_id": rule_id,
                    "result": "pass",
                    "source_id": str(source.id),
                    "port_call_id": str(port_call.id),
                },
            )

    logger.info(
        "Leakage audit for source %s: %d anomalies (LD-001..LD-004)",
        source.id,
        len(created),
    )
    return created


__all__ = [
    "run_audit",
]
