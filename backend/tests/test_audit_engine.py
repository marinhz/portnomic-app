"""Tests for Sentinel AuditEngine and Triple-Check rules (Task 14.4)."""

import uuid
from datetime import datetime, timezone

import pytest

from app.database import async_session_factory
from app.models.disbursement_account import DisbursementAccount
from app.models.email import Email
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tenant import Tenant
from app.models.vessel import Vessel
from app.services.sentinel import AuditEngine, get_timeline_events
from app.services.sentinel.audit_engine import (
    _rule_s001_temporal_tug_pilot,
    _rule_s002_berthage_stay,
    _rule_s003_fuel_paradox,
)
from app.services.sentinel.models import EventSource, TimelineEvent


# --- Rule S-001: Temporal Tug/Pilot ---


def test_s001_flags_overcharged_tug_hours():
    """S-001 flags when DA invoiced hours > SOF actual + 0.5hr buffer."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = [
        TimelineEvent(
            source=EventSource.DA,
            source_document_id=doc_id,
            start=datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc),
            event_type="tug_service",
            raw_data={"quantity": 5.0, "amount": 2500},
            port_call_id=pc_id,
        ),
        TimelineEvent(
            source=EventSource.SOF,
            source_document_id=uuid.uuid4(),
            start=datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 11, 0, 0, tzinfo=timezone.utc),
            event_type="tug_service",
            raw_data={},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s001_temporal_tug_pilot(events)
    assert len(findings) == 1
    assert "Overcharged tug hours" in findings[0]["description"]
    assert "5.0" in findings[0]["description"]
    assert "3.0" in findings[0]["description"]  # SOF 3h


def test_s001_no_flag_when_within_buffer():
    """S-001 does not flag when DA hours within SOF + buffer."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = [
        TimelineEvent(
            source=EventSource.DA,
            source_document_id=doc_id,
            start=datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 11, 0, 0, tzinfo=timezone.utc),
            event_type="tug_service",
            raw_data={"quantity": 3.0},
            port_call_id=pc_id,
        ),
        TimelineEvent(
            source=EventSource.SOF,
            source_document_id=uuid.uuid4(),
            start=datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 3, 11, 11, 0, 0, tzinfo=timezone.utc),
            event_type="tug_service",
            raw_data={},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s001_temporal_tug_pilot(events)
    assert len(findings) == 0


# --- Rule S-002: Berthage/Stay ---


def test_s002_flags_berth_mismatch_with_eta_etd_stub():
    """S-002 flags when DA berth days != eta/etd-derived days."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    eta = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    etd = datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc)
    events = [
        TimelineEvent(
            source=EventSource.DA,
            source_document_id=doc_id,
            start=eta,
            end=etd,
            event_type="berth_fee_days",
            raw_data={"quantity": 5.0},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s002_berthage_stay(events, eta=eta, etd=etd)
    assert len(findings) == 1
    assert "Berthage mismatch" in findings[0]["description"]
    # eta to etd = 2d 10h ≈ 2.42 days
    assert "5.0" in findings[0]["description"]


def test_s002_no_flag_when_days_match():
    """S-002 does not flag when DA days match actual."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    eta = datetime(2026, 3, 10, 0, 0, 0, tzinfo=timezone.utc)
    etd = datetime(2026, 3, 13, 0, 0, 0, tzinfo=timezone.utc)
    events = [
        TimelineEvent(
            source=EventSource.DA,
            source_document_id=doc_id,
            start=eta,
            end=etd,
            event_type="berth_fee_days",
            raw_data={"quantity": 3.0},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s002_berthage_stay(events, eta=eta, etd=etd)
    assert len(findings) == 0


def test_s002_uses_ais_berth_events_when_available():
    """S-002 compares DA berth days vs AIS berth stay duration when AIS events present."""
    doc_id = uuid.uuid4()
    ais_doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    arrival = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    departure = datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc)
    events = [
        TimelineEvent(
            source=EventSource.DA,
            source_document_id=doc_id,
            start=arrival,
            end=departure,
            event_type="berth_fee_days",
            raw_data={"quantity": 5.0},
            port_call_id=pc_id,
        ),
        TimelineEvent(
            source=EventSource.AIS,
            source_document_id=ais_doc_id,
            start=arrival,
            end=departure,
            event_type="berth_arrival",
            raw_data={},
            port_call_id=pc_id,
        ),
        TimelineEvent(
            source=EventSource.AIS,
            source_document_id=ais_doc_id,
            start=departure,
            end=None,
            event_type="berth_departure",
            raw_data={},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s002_berthage_stay(events)
    assert len(findings) == 1
    assert "Berthage mismatch" in findings[0]["description"]
    assert "ais" in findings[0]["raw_evidence"]["source"]


# --- Rule S-003: Fuel Paradox ---


def test_s003_flags_high_fuel_during_idle():
    """S-003 flags high fuel consumption during idle at anchorage 12+ hrs."""
    pc_id = uuid.uuid4()
    idle_start = datetime(2026, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
    idle_end = datetime(2026, 3, 11, 14, 0, 0, tzinfo=timezone.utc)
    fuel_time = datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc)
    events = [
        TimelineEvent(
            source=EventSource.SOF,
            source_document_id=uuid.uuid4(),
            start=idle_start,
            end=idle_end,
            event_type="idle_at_anchorage",
            raw_data={},
            port_call_id=pc_id,
        ),
        TimelineEvent(
            source=EventSource.NOON_REPORT,
            source_document_id=uuid.uuid4(),
            start=fuel_time,
            end=None,
            event_type="fuel_consumption",
            raw_data={"consumption_mt": 3.0, "operational_status": "at_anchor"},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s003_fuel_paradox(events)
    assert len(findings) == 1
    assert "Unusual fuel burn" in findings[0]["description"]


def test_s003_no_flag_when_low_fuel():
    """S-003 does not flag when fuel consumption is low."""
    pc_id = uuid.uuid4()
    idle_start = datetime(2026, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
    idle_end = datetime(2026, 3, 11, 14, 0, 0, tzinfo=timezone.utc)
    events = [
        TimelineEvent(
            source=EventSource.SOF,
            source_document_id=uuid.uuid4(),
            start=idle_start,
            end=idle_end,
            event_type="idle_at_anchorage",
            raw_data={},
            port_call_id=pc_id,
        ),
        TimelineEvent(
            source=EventSource.NOON_REPORT,
            source_document_id=uuid.uuid4(),
            start=datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc),
            end=None,
            event_type="fuel_consumption",
            raw_data={"consumption_mt": 0.5},
            port_call_id=pc_id,
        ),
    ]
    findings = _rule_s003_fuel_paradox(events)
    assert len(findings) == 0


# --- AuditEngine integration ---


@pytest.mark.asyncio
async def test_audit_engine_returns_report_and_persists():
    """AuditEngine.compare_events returns AuditReport and persists discrepancies."""
    async with async_session_factory() as db:
        tenant = Tenant(
            name="Audit Test Tenant",
            slug=f"audit-test-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="Test Vessel", imo="1234567")
        port = Port(tenant_id=tenant.id, name="Test Port", code="TST")
        db.add(vessel)
        db.add(port)
        await db.flush()

        eta = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
        etd = datetime(2026, 3, 13, 18, 0, 0, tzinfo=timezone.utc)
        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=eta,
            etd=etd,
        )
        db.add(port_call)
        await db.flush()

        da = DisbursementAccount(
            tenant_id=tenant.id,
            port_call_id=port_call.id,
            type="final",
            status="draft",
            line_items=[
                {
                    "description": "Tug service",
                    "quantity": 6.0,
                    "amount": 3000,
                    "service_date": "2026-03-10T08:00:00Z",
                },
                {"description": "Berthage", "quantity": 5.0},
            ],
            totals={"subtotal": 3500, "tax": 0, "total": 3500, "currency": "USD"},
        )
        db.add(da)
        await db.flush()

        email = Email(
            tenant_id=tenant.id,
            port_call_id=port_call.id,
            external_id=f"audit-email-{uuid.uuid4().hex}",
            ai_raw_output={
                "sof_timestamps": {
                    "tug_fast": "2026-03-10T08:00:00Z",
                    "tug_off": "2026-03-10T12:00:00Z",
                },
            },
        )
        db.add(email)
        await db.flush()

        engine = AuditEngine(db, tenant.id)
        report = await engine.compare_events(port_call.id)
        await db.commit()

    assert report.total_count >= 1
    assert report.rules_executed == ["S-001", "S-002", "S-003"]
    assert isinstance(report.by_severity, dict)
    assert len(report.discrepancies) == report.total_count


@pytest.mark.asyncio
async def test_audit_engine_nonexistent_port_call():
    """AuditEngine returns empty report for nonexistent port call."""
    async with async_session_factory() as db:
        tenant = Tenant(
            name="T2",
            slug=f"t2-{uuid.uuid4().hex[:8]}",
        )
        db.add(tenant)
        await db.flush()
        engine = AuditEngine(db, tenant.id)
        report = await engine.compare_events(uuid.uuid4())
        await db.commit()

    assert report.total_count == 0
    assert report.discrepancies == []
    assert report.rules_executed == ["S-001", "S-002", "S-003"]
