"""Tests for AIS normalizer — Task 14.5."""

import uuid
from datetime import datetime, timezone

import pytest

from app.services.sentinel.ais_client import BerthData
from app.services.sentinel.ais_normalizer import normalize_ais
from app.services.sentinel.models import EventSource


def test_normalize_ais_with_berth_data_produces_events():
    """normalize_ais with BerthData produces berth_arrival and berth_departure TimelineEvents."""
    pc_id = uuid.uuid4()
    arrival = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    departure = datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc)
    berth_data = BerthData(
        berth_arrival=arrival,
        berth_departure=departure,
        raw_positions_count=12,
    )

    events = normalize_ais(berth_data=berth_data, port_call_id=pc_id)

    assert len(events) == 2
    berth_arr = next(e for e in events if e.event_type == "berth_arrival")
    berth_dep = next(e for e in events if e.event_type == "berth_departure")

    assert berth_arr.source == EventSource.AIS
    assert berth_arr.start == arrival
    assert berth_arr.end == departure
    assert berth_arr.raw_data["raw_positions_count"] == 12

    assert berth_dep.source == EventSource.AIS
    assert berth_dep.start == departure
    assert berth_dep.end is None


def test_normalize_ais_with_none_returns_empty():
    """normalize_ais with berth_data=None returns empty list."""
    pc_id = uuid.uuid4()
    events = normalize_ais(berth_data=None, port_call_id=pc_id)
    assert events == []


def test_normalize_ais_with_legacy_ais_data_dict():
    """normalize_ais accepts legacy ais_data dict for berth_arrival/berth_departure."""
    pc_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    ais_data = {
        "berth_arrival": "2026-03-10T08:00:00+00:00",
        "berth_departure": "2026-03-12T18:00:00+00:00",
    }

    events = normalize_ais(
        ais_data=ais_data,
        source_document_id=doc_id,
        port_call_id=pc_id,
    )

    assert len(events) == 2
    berth_arr = next(e for e in events if e.event_type == "berth_arrival")
    assert berth_arr.source_document_id == doc_id
    assert berth_arr.start.isoformat().startswith("2026-03-10T08:00:00")
    assert berth_arr.end.isoformat().startswith("2026-03-12T18:00:00")
