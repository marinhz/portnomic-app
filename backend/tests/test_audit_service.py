"""Tests for AuditService (AI Leakage Detector LD-001 through LD-004)."""

from datetime import datetime, timezone

from app.services.audit_service import (
    _ld001_temporal_validation,
    _ld002_duplicate_detection,
    _ld003_tariff_shift,
    _ld004_quantity_variance,
)


def test_ld001_temporal_before_eta():
    """LD-001: Service date before ETA should flag anomaly."""
    eta = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    etd = datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc)
    line_items = [
        {"description": "Pilotage", "amount": 500, "service_date": "2026-03-09T10:00:00Z"},
    ]
    anomalies = _ld001_temporal_validation(line_items, eta, etd)
    assert len(anomalies) == 1
    assert anomalies[0]["rule_id"] == "LD-001"
    assert "before vessel ETA" in anomalies[0]["description"]
    assert anomalies[0]["severity"] == "high"


def test_ld001_temporal_after_etd():
    """LD-001: Service date after ETD should flag anomaly."""
    eta = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    etd = datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc)
    line_items = [
        {"description": "Tug", "amount": 1200, "service_date": "2026-03-13T10:00:00Z"},
    ]
    anomalies = _ld001_temporal_validation(line_items, eta, etd)
    assert len(anomalies) == 1
    assert "after vessel ETD" in anomalies[0]["description"]


def test_ld001_temporal_within_range_no_anomaly():
    """LD-001: Service date within eta/etd should not flag."""
    eta = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    etd = datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc)
    line_items = [
        {"description": "Pilotage", "amount": 500, "service_date": "2026-03-11T10:00:00Z"},
    ]
    anomalies = _ld001_temporal_validation(line_items, eta, etd)
    assert len(anomalies) == 0


def test_ld002_duplicate_detection():
    """LD-002: Duplicate description+amount should flag."""
    all_items = [
        {"description": "Tug service", "amount": 1200},
        {"description": "Tug service", "amount": 1200},
    ]
    anomalies = _ld002_duplicate_detection(all_items)
    assert len(anomalies) == 1
    assert anomalies[0]["rule_id"] == "LD-002"
    assert "Duplicate" in anomalies[0]["description"]


def test_ld002_no_duplicate():
    """LD-002: Unique items should not flag."""
    all_items = [
        {"description": "Tug service", "amount": 1200},
        {"description": "Pilotage", "amount": 500},
    ]
    anomalies = _ld002_duplicate_detection(all_items)
    assert len(anomalies) == 0


def test_ld003_weekend_rate_on_weekday():
    """LD-003: Weekend rate on weekday should flag."""
    line_items = [
        {
            "description": "Tug - Weekend rate",
            "amount": 1500,
            "service_date": "2026-03-11T10:00:00Z",  # Tuesday
        },
    ]
    anomalies = _ld003_tariff_shift(line_items)
    assert len(anomalies) == 1
    assert anomalies[0]["rule_id"] == "LD-003"
    assert "weekday" in anomalies[0]["description"]


def test_ld003_weekend_rate_on_saturday_no_anomaly():
    """LD-003: Weekend rate on Saturday should not flag."""
    line_items = [
        {
            "description": "Tug - Weekend rate",
            "amount": 1500,
            "service_date": "2026-03-14T10:00:00Z",  # Saturday
        },
    ]
    anomalies = _ld003_tariff_shift(line_items)
    assert len(anomalies) == 0


def test_ld004_tug_hours_exceeds_limit():
    """LD-004: Tug/pilot hours > 24h should flag."""
    line_items = [
        {"description": "Tug service", "amount": 3000, "quantity": 15},
        {"description": "Pilotage", "amount": 500, "quantity": 12},
    ]
    anomalies = _ld004_quantity_variance(line_items, emission_reports=[], vessel=None)
    assert len(anomalies) == 1
    assert anomalies[0]["rule_id"] == "LD-004"
    assert "24h" in anomalies[0]["description"]
