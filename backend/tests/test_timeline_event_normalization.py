"""Tests for Sentinel TimelineEvent model and normalizers (Task 14.2)."""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.database import async_session_factory
from app.models.disbursement_account import DisbursementAccount
from app.models.emission_report import EmissionReport
from app.models.email import Email
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tenant import Tenant
from app.models.vessel import Vessel
from app.services.sentinel import TimelineEvent, get_timeline_events
from app.services.sentinel.ais_normalizer import normalize_ais
from app.services.sentinel.da_normalizer import normalize_da_line_items
from app.services.sentinel.models import EventSource as EventSourceEnum
from app.services.sentinel.timeline_aggregator import get_timeline_events
from app.services.sentinel.noon_report_normalizer import normalize_noon_report
from app.services.sentinel.sof_normalizer import normalize_sof


# --- DA normalizer ---


def test_da_normalizer_tug_service():
    """DA normalizer extracts tug_service from line items."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = normalize_da_line_items(
        line_items=[
            {"description": "Tug service", "quantity": 4.0, "amount": 2000, "service_date": "2026-03-11T08:00:00Z"},
        ],
        source_document_id=doc_id,
        port_call_id=pc_id,
    )
    assert len(events) == 1
    e = events[0]
    assert e.source == EventSourceEnum.DA
    assert e.source_document_id == doc_id
    assert e.port_call_id == pc_id
    assert e.event_type == "tug_service"
    assert e.start == datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc)
    assert e.end == datetime(2026, 3, 11, 12, 0, 0, tzinfo=timezone.utc)
    assert e.raw_data["quantity"] == 4.0


def test_da_normalizer_pilot_uses_eta_when_no_service_date():
    """DA normalizer uses eta when service_date is missing."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = normalize_da_line_items(
        line_items=[
            {"description": "Pilotage", "quantity": 2.0, "amount": 500},
        ],
        source_document_id=doc_id,
        port_call_id=pc_id,
        eta="2026-03-10T06:00:00Z",
    )
    assert len(events) == 1
    assert events[0].start == datetime(2026, 3, 10, 6, 0, 0, tzinfo=timezone.utc)
    assert events[0].end == datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)


def test_da_normalizer_skips_unknown_line_items():
    """DA normalizer skips line items that don't map to event types."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = normalize_da_line_items(
        line_items=[
            {"description": "Agency fee", "amount": 1500},
        ],
        source_document_id=doc_id,
        port_call_id=pc_id,
        eta="2026-03-10T06:00:00Z",
    )
    assert len(events) == 0


# --- SOF normalizer ---


def test_sof_normalizer_tug_and_pilot():
    """SOF normalizer parses tug_fast/tug_off and pilot_on/pilot_off."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    sof_data = {
        "tug_fast": "2026-03-11T08:00:00Z",
        "tug_off": "2026-03-11T12:30:00Z",
        "pilot_on": "2026-03-11T07:30:00Z",
        "pilot_off": "2026-03-11T09:30:00Z",
    }
    events = normalize_sof(sof_data=sof_data, source_document_id=doc_id, port_call_id=pc_id)
    assert len(events) == 2

    tug = next(e for e in events if e.event_type == "tug_service")
    assert tug.start == datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc)
    assert tug.end == datetime(2026, 3, 11, 12, 30, 0, tzinfo=timezone.utc)
    assert tug.source == EventSourceEnum.SOF

    pilot = next(e for e in events if e.event_type == "pilot_service")
    assert pilot.start == datetime(2026, 3, 11, 7, 30, 0, tzinfo=timezone.utc)
    assert pilot.end == datetime(2026, 3, 11, 9, 30, 0, tzinfo=timezone.utc)


def test_sof_normalizer_idle_at_anchorage():
    """SOF normalizer parses idle_at_anchorage_start/end."""
    doc_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    sof_data = {
        "idle_at_anchorage_start": "2026-03-10T14:00:00Z",
        "idle_at_anchorage_end": "2026-03-11T08:00:00Z",
    }
    events = normalize_sof(sof_data=sof_data, source_document_id=doc_id, port_call_id=pc_id)
    assert len(events) == 1
    assert events[0].event_type == "idle_at_anchorage"
    assert events[0].start == datetime(2026, 3, 10, 14, 0, 0, tzinfo=timezone.utc)
    assert events[0].end == datetime(2026, 3, 11, 8, 0, 0, tzinfo=timezone.utc)


# --- Noon Report normalizer ---


def test_noon_report_normalizer_fuel_consumption():
    """Noon Report normalizer extracts fuel_consumption events."""
    report_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = normalize_noon_report(
        report_id=report_id,
        port_call_id=pc_id,
        report_date=date(2026, 3, 11),
        fuel_entries=[
            {"fuel_type": "VLSFO", "consumption_mt": 12.5, "operational_status": "at_berth"},
        ],
    )
    assert len(events) == 1
    assert events[0].event_type == "fuel_consumption"
    assert events[0].source == EventSourceEnum.NOON_REPORT
    assert events[0].source_document_id == report_id
    assert events[0].raw_data["consumption_mt"] == 12.5


def test_noon_report_normalizer_at_anchor_maps_to_idle():
    """Noon Report at_anchor maps to idle_at_anchorage event type."""
    report_id = uuid.uuid4()
    pc_id = uuid.uuid4()
    events = normalize_noon_report(
        report_id=report_id,
        port_call_id=pc_id,
        report_date=date(2026, 3, 11),
        fuel_entries=[
            {"fuel_type": "MGO", "consumption_mt": 2.0, "operational_status": "at_anchor"},
        ],
    )
    assert len(events) == 1
    assert events[0].event_type == "idle_at_anchorage"


# --- AIS normalizer ---


def test_ais_normalizer_placeholder():
    """AIS normalizer returns empty list (Task 14.5 placeholder)."""
    pc_id = uuid.uuid4()
    events = normalize_ais(port_call_id=pc_id)
    assert events == []


# --- get_timeline_events aggregator ---


@pytest.mark.asyncio
async def test_get_timeline_events_returns_sorted():
    """get_timeline_events returns merged events sorted by start."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test",
            slug=f"test-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="MV Test")
        db.add(vessel)
        await db.flush()

        port = Port(tenant_id=tenant.id, name="Rotterdam", code="NLRTM")
        db.add(port)
        await db.flush()

        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
            etd=datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc),
        )
        db.add(port_call)
        await db.flush()

        da = DisbursementAccount(
            tenant_id=tenant.id,
            port_call_id=port_call.id,
            type="final",
            status="draft",
            line_items=[
                {"description": "Tug service", "quantity": 4.0, "amount": 2000, "service_date": "2026-03-11T10:00:00Z"},
                {"description": "Pilotage", "quantity": 2.0, "amount": 500, "service_date": "2026-03-11T08:00:00Z"},
            ],
            totals={"subtotal": 2500, "tax": 0, "total": 2500, "currency": "USD"},
        )
        db.add(da)
        await db.flush()

        events = await get_timeline_events(db, port_call.id, tenant.id)
        assert len(events) >= 2
        # Pilot at 08:00, Tug at 10:00 — pilot should be first
        assert events[0].start <= events[1].start
        assert all(isinstance(e, TimelineEvent) for e in events)

        await db.rollback()


@pytest.mark.asyncio
async def test_get_timeline_events_nonexistent_port_call():
    """get_timeline_events returns [] for nonexistent port call."""
    async with async_session_factory() as db:
        tenant_id = uuid.uuid4()
        port_call_id = uuid.uuid4()
        events = await get_timeline_events(db, port_call_id, tenant_id)
        assert events == []
