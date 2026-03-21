"""
AuditEngine — runs Triple-Check algorithm (Rules S-001, S-002, S-003) using normalized
TimelineEvents, time_overlap logic, and persisted Discrepancy records.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discrepancy import Discrepancy
from app.models.port_call import PortCall
from app.schemas.discrepancy import DiscrepancyResponse
from app.services.audit import log_action
from app.services.sentinel.models import EventSource, TimelineEvent
from app.services.sentinel.time_overlap import time_overlap_detail
from app.services.sentinel.timeline_aggregator import get_timeline_events

# Rule constants
S001_BUFFER_HOURS = 0.5
S003_IDLE_THRESHOLD_HOURS = 12.0
S003_HIGH_FUEL_THRESHOLD_MT = 2.0

RULE_IDS = ("S-001", "S-002", "S-003")


@dataclass
class AuditReport:
    """Result of an AuditEngine run — discrepancies and summary counts."""

    discrepancies: list[DiscrepancyResponse]
    total_count: int
    by_severity: dict[str, int]
    by_rule: dict[str, int]
    rules_executed: list[str]


class AuditEngine:
    """
    Sentinel audit engine — compares DA, SOF, Noon Report, and AIS data
    via the Triple-Check algorithm and persists findings.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    async def compare_events(self, port_call_id: uuid.UUID) -> AuditReport:
        """
        Run Triple-Check rules on port call timeline events.
        Returns AuditReport with discrepancies (persisted) and summary.
        """
        events = await get_timeline_events(self.db, port_call_id, self.tenant_id)

        # Load port call for S-002 stub (eta/etd when AIS unavailable)
        pc_result = await self.db.execute(
            select(PortCall).where(
                PortCall.id == port_call_id,
                PortCall.tenant_id == self.tenant_id,
            )
        )
        port_call = pc_result.scalar_one_or_none()
        eta = port_call.eta if port_call else None
        etd = port_call.etd if port_call else None

        discrepancies: list[DiscrepancyResponse] = []

        # S-001: Temporal Tug/Pilot Audit
        s001_findings = _rule_s001_temporal_tug_pilot(events)
        for d in s001_findings:
            created = await self._persist_discrepancy(
                port_call_id=port_call_id,
                rule_id="S-001",
                severity="high",
                description=d["description"],
                source_documents=d["source_documents"],
                estimated_loss=d.get("estimated_loss"),
                raw_evidence=d.get("raw_evidence"),
            )
            discrepancies.append(created)

        # S-002: Berthage/Stay Verification (uses eta/etd stub when AIS unavailable)
        s002_findings = _rule_s002_berthage_stay(events, eta=eta, etd=etd)
        for d in s002_findings:
            created = await self._persist_discrepancy(
                port_call_id=port_call_id,
                rule_id="S-002",
                severity="medium",
                description=d["description"],
                source_documents=d["source_documents"],
                estimated_loss=d.get("estimated_loss"),
                raw_evidence=d.get("raw_evidence"),
            )
            discrepancies.append(created)

        # S-003: Fuel Consumption Paradox
        s003_findings = _rule_s003_fuel_paradox(events)
        for d in s003_findings:
            created = await self._persist_discrepancy(
                port_call_id=port_call_id,
                rule_id="S-003",
                severity="medium",
                description=d["description"],
                source_documents=d["source_documents"],
                estimated_loss=None,
                raw_evidence=d.get("raw_evidence"),
            )
            discrepancies.append(created)

        # Summary
        by_severity: dict[str, int] = {}
        for disc in discrepancies:
            by_severity[disc.severity] = by_severity.get(disc.severity, 0) + 1

        by_rule: dict[str, int] = {}
        for disc in discrepancies:
            rid = disc.rule_id or "unknown"
            by_rule[rid] = by_rule.get(rid, 0) + 1

        # AuditLog
        await log_action(
            self.db,
            tenant_id=self.tenant_id,
            user_id=None,
            action="sentinel_audit",
            resource_type="port_call",
            resource_id=str(port_call_id),
            payload={
                "rules_executed": list(RULE_IDS),
                "discrepancy_count": len(discrepancies),
                "by_severity": by_severity,
                "by_rule": by_rule,
            },
        )

        return AuditReport(
            discrepancies=discrepancies,
            total_count=len(discrepancies),
            by_severity=by_severity,
            by_rule=by_rule,
            rules_executed=list(RULE_IDS),
        )

    async def _persist_discrepancy(
        self,
        *,
        port_call_id: uuid.UUID,
        rule_id: str,
        severity: str,
        description: str,
        source_documents: list[uuid.UUID],
        estimated_loss: Decimal | None,
        raw_evidence: dict | None,
    ) -> DiscrepancyResponse:
        """Create and persist a Discrepancy, return response schema."""
        obj = Discrepancy(
            tenant_id=self.tenant_id,
            port_call_id=port_call_id,
            source_documents=source_documents,
            severity=severity,
            estimated_loss=estimated_loss,
            description=description,
            rule_id=rule_id,
            raw_evidence=raw_evidence,
        )
        self.db.add(obj)
        await self.db.flush()
        return DiscrepancyResponse.model_validate(obj)


def _rule_s001_temporal_tug_pilot(events: list[TimelineEvent]) -> list[dict]:
    """
    S-001: DA invoiced hours vs SOF tug/pilot timestamps.
    Flag if DA > (SOF duration) + 0.5hr buffer.
    Uses time_overlap for temporal validation.
    """
    findings: list[dict] = []
    da_tug = [e for e in events if e.source == EventSource.DA and e.event_type == "tug_service"]
    sof_tug = [e for e in events if e.source == EventSource.SOF and e.event_type == "tug_service"]
    da_pilot = [
        e for e in events if e.source == EventSource.DA and e.event_type == "pilot_service"
    ]
    sof_pilot = [
        e for e in events if e.source == EventSource.SOF and e.event_type == "pilot_service"
    ]

    # Tug: compare DA tug hours vs SOF tug interval
    for da in da_tug:
        da_hours = da.raw_data.get("quantity") or 0.0
        da_end = da.end or da.start
        source_docs = [da.source_document_id]

        for sof in sof_tug:
            sof_start = sof.start
            sof_end = sof.end or sof.start
            sof_hours = (sof_end - sof_start).total_seconds() / 3600.0

            detail = time_overlap_detail(
                da.start, da_end, sof_start, sof_end, buffer_hours=S001_BUFFER_HOURS
            )
            # Overcharge: DA invoiced more than SOF actual + buffer
            if da_hours > sof_hours + S001_BUFFER_HOURS and detail.overlaps:
                amount = da.raw_data.get("amount")
                findings.append({
                    "description": (
                        f"Overcharged tug hours: DA invoiced {da_hours:.1f}h, "
                        f"SOF actual {sof_hours:.1f}h (buffer {S001_BUFFER_HOURS}h). "
                        "High Risk: Overcharged Service Hours."
                    ),
                    "source_documents": source_docs + [sof.source_document_id],
                    "estimated_loss": Decimal(str(amount)) if amount is not None else None,
                    "raw_evidence": {
                        "da_hours": da_hours,
                        "sof_hours": sof_hours,
                        "buffer_hours": S001_BUFFER_HOURS,
                        "da_start": da.start.isoformat(),
                        "da_end": (da_end).isoformat(),
                        "sof_start": sof_start.isoformat(),
                        "sof_end": sof_end.isoformat(),
                    },
                })
                break

        # No matching SOF — check if we have any SOF at all for tug
        if not sof_tug and da_hours > S001_BUFFER_HOURS:
            findings.append({
                "description": (
                    f"Tug hours invoiced ({da_hours:.1f}h) but no SOF tug timestamps "
                    "available for verification. Manual review recommended."
                ),
                "source_documents": source_docs,
                "estimated_loss": Decimal(str(da.raw_data.get("amount")))
                if da.raw_data.get("amount") is not None
                else None,
                "raw_evidence": {"da_hours": da_hours, "sof_events": 0},
            })

    # Pilot: same logic
    for da in da_pilot:
        da_hours = da.raw_data.get("quantity") or 0.0
        da_end = da.end or da.start
        source_docs = [da.source_document_id]

        for sof in sof_pilot:
            sof_start = sof.start
            sof_end = sof.end or sof.start
            sof_hours = (sof_end - sof_start).total_seconds() / 3600.0

            detail = time_overlap_detail(
                da.start, da_end, sof_start, sof_end, buffer_hours=S001_BUFFER_HOURS
            )
            if da_hours > sof_hours + S001_BUFFER_HOURS and detail.overlaps:
                amount = da.raw_data.get("amount")
                findings.append({
                    "description": (
                        f"Overcharged pilot hours: DA invoiced {da_hours:.1f}h, "
                        f"SOF actual {sof_hours:.1f}h (buffer {S001_BUFFER_HOURS}h). "
                        "High Risk: Overcharged Service Hours."
                    ),
                    "source_documents": source_docs + [sof.source_document_id],
                    "estimated_loss": Decimal(str(amount)) if amount is not None else None,
                    "raw_evidence": {
                        "da_hours": da_hours,
                        "sof_hours": sof_hours,
                        "buffer_hours": S001_BUFFER_HOURS,
                    },
                })
                break

        if not sof_pilot and da_hours > S001_BUFFER_HOURS:
            findings.append({
                "description": (
                    f"Pilot hours invoiced ({da_hours:.1f}h) but no SOF pilot timestamps "
                    "available for verification. Manual review recommended."
                ),
                "source_documents": source_docs,
                "estimated_loss": Decimal(str(da.raw_data.get("amount")))
                if da.raw_data.get("amount") is not None
                else None,
                "raw_evidence": {"da_hours": da_hours, "sof_events": 0},
            })

    return findings


def _rule_s002_berthage_stay(
    events: list[TimelineEvent],
    eta: datetime | None = None,
    etd: datetime | None = None,
) -> list[dict]:
    """
    S-002: DA berth fee days vs AIS berth stay duration.
    When AIS is unavailable (Task 14.5 stub), use eta/etd as "actual" berth duration.
    """
    findings: list[dict] = []
    da_berth = [
        e for e in events if e.source == EventSource.DA and e.event_type == "berth_fee_days"
    ]
    ais_berth_arr = [
        e for e in events if e.source == EventSource.AIS and e.event_type == "berth_arrival"
    ]
    ais_berth_dep = [
        e for e in events if e.source == EventSource.AIS and e.event_type == "berth_departure"
    ]

    # Resolve actual berth duration: AIS if available, else eta/etd stub
    if ais_berth_arr or ais_berth_dep:
        ais_start = min(e.start for e in ais_berth_arr) if ais_berth_arr else None
        ais_end = max(e.start for e in ais_berth_dep) if ais_berth_dep else None
        if ais_start and ais_end and ais_end > ais_start:
            actual_days = (ais_end - ais_start).total_seconds() / 86400.0
            actual_source = "ais"
            source_doc_ids = [e.source_document_id for e in ais_berth_arr + ais_berth_dep]
        else:
            return []
    elif eta and etd and etd > eta:
        actual_days = (etd - eta).total_seconds() / 86400.0
        actual_source = "eta_etd_stub"
        source_doc_ids = []
    else:
        return []  # No AIS or eta/etd to compare

    for da in da_berth:
        da_days = da.raw_data.get("quantity") or 0.0
        if abs(da_days - actual_days) > 0.5:  # More than half-day variance
            source_docs = list({da.source_document_id} | set(source_doc_ids))
            findings.append({
                "description": (
                    f"Berthage mismatch: DA claims {da_days:.1f} days, "
                    f"actual berth stay {actual_days:.1f} days ({actual_source}). "
                    "Potential Error: Incorrect Berthage Calculation."
                ),
                "source_documents": source_docs,
                "estimated_loss": None,
                "raw_evidence": {
                    "da_days": da_days,
                    "actual_days": actual_days,
                    "source": actual_source,
                },
            })

    return findings


def _rule_s003_fuel_paradox(events: list[TimelineEvent]) -> list[dict]:
    """
    S-003: High noon fuel consumption + SOF "Idle at Anchorage" 12+ hrs.
    Cross-reference fuel events with idle events.
    """
    findings: list[dict] = []
    fuel_events = [
        e for e in events
        if e.source == EventSource.NOON_REPORT and e.event_type == "fuel_consumption"
    ]
    idle_events = [
        e for e in events
        if e.source == EventSource.SOF and e.event_type == "idle_at_anchorage" and e.end
    ]

    for idle in idle_events:
        idle_end = idle.end or idle.start
        idle_hours = (idle_end - idle.start).total_seconds() / 3600.0
        if idle_hours < S003_IDLE_THRESHOLD_HOURS:
            continue

        for fuel in fuel_events:
            consumption = fuel.raw_data.get("consumption_mt")
            try:
                consumption_mt = float(consumption) if consumption is not None else 0.0
            except (ValueError, TypeError):
                consumption_mt = 0.0

            if consumption_mt < S003_HIGH_FUEL_THRESHOLD_MT:
                continue

            # Check if fuel report falls within idle period (point-in-time)
            if idle.start <= fuel.start <= idle_end:
                source_docs = list({idle.source_document_id, fuel.source_document_id})
                findings.append({
                    "description": (
                        f"Unusual fuel burn while idle: {consumption_mt:.2f} MT reported "
                        f"during {idle_hours:.1f}h idle at anchorage. "
                        "Operational Alert: Unusual Fuel Burn while Idle."
                    ),
                    "source_documents": source_docs,
                    "raw_evidence": {
                        "fuel_consumption_mt": consumption_mt,
                        "idle_hours": idle_hours,
                        "fuel_report_date": fuel.start.isoformat(),
                        "idle_start": idle.start.isoformat(),
                        "idle_end": idle_end.isoformat(),
                    },
                })
                break

    return findings
