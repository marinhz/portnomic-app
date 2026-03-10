"""Tests for emission anomaly detection (AI Auditor)."""

import uuid
from datetime import date

from app.models.emission_report import EmissionReport, FuelEntry
from app.models.vessel import Vessel
from app.services.emission_anomaly import run_anomaly_checks


def _make_report(
    distance_nm: float | None = 100.0,
    fuel_entries: list[tuple[str, float, str]] | None = None,
) -> EmissionReport:
    """Create a minimal EmissionReport for testing."""
    report = EmissionReport(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        vessel_id=uuid.uuid4(),
        report_date=date.today(),
        distance_nm=distance_nm,
    )
    if fuel_entries:
        report.fuel_entries = [
            FuelEntry(
                id=uuid.uuid4(),
                emission_report_id=report.id,
                fuel_type=ft,
                consumption_mt=cons,
                operational_status=status,
            )
            for ft, cons, status in fuel_entries
        ]
    else:
        report.fuel_entries = []
    return report


def _make_vessel(allowed_fuel_types: list[str] | None = None) -> Vessel:
    """Create a minimal Vessel for testing."""
    v = Vessel(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Test Vessel",
    )
    v.allowed_fuel_types = allowed_fuel_types
    return v


def test_consumption_vs_distance_high_ratio():
    """Flag when consumption/distance ratio exceeds plausible max."""
    # 50 MT over 100 NM = 0.5 MT/NM (expected max ~0.2)
    report = _make_report(
        distance_nm=100.0,
        fuel_entries=[("VLSFO", 50.0, "at_sea_cruising")],
    )
    flags = run_anomaly_checks(report, None)
    assert len(flags) >= 1
    assert any(f["rule"] == "consumption_vs_distance" for f in flags)


def test_consumption_vs_distance_low_ratio():
    """Flag when consumption/distance ratio is below plausible min."""
    # 0.001 MT over 100 NM = 0.00001 MT/NM (expected min ~0.002)
    report = _make_report(
        distance_nm=100.0,
        fuel_entries=[("VLSFO", 0.001, "at_sea_cruising")],
    )
    flags = run_anomaly_checks(report, None)
    assert len(flags) >= 1
    assert any(f["rule"] == "consumption_vs_distance" for f in flags)


def test_consumption_vs_distance_plausible_no_flag():
    """No flag when ratio is within plausible range."""
    # 5 MT over 100 NM = 0.05 MT/NM (within 0.002–0.2)
    report = _make_report(
        distance_nm=100.0,
        fuel_entries=[("VLSFO", 5.0, "at_sea_cruising")],
    )
    flags = run_anomaly_checks(report, None)
    consumption_flags = [f for f in flags if f["rule"] == "consumption_vs_distance"]
    assert len(consumption_flags) == 0


def test_consumption_vs_distance_skipped_when_no_distance():
    """Skip rule when distance is None or zero."""
    report = _make_report(
        distance_nm=None,
        fuel_entries=[("VLSFO", 50.0, "at_sea_cruising")],
    )
    flags = run_anomaly_checks(report, None)
    consumption_flags = [f for f in flags if f["rule"] == "consumption_vs_distance"]
    assert len(consumption_flags) == 0


def test_fuel_type_mismatch_when_profile_exists():
    """Flag when reported fuel type not in vessel profile."""
    report = _make_report(
        fuel_entries=[("LNG", 1.0, "at_berth")],
    )
    vessel = _make_vessel(allowed_fuel_types=["VLSFO", "MGO"])
    flags = run_anomaly_checks(report, vessel)
    assert len(flags) >= 1
    assert any(f["rule"] == "fuel_type_mismatch" for f in flags)


def test_fuel_type_ok_when_in_profile():
    """No flag when reported fuel type is in vessel profile."""
    report = _make_report(
        fuel_entries=[("VLSFO", 5.0, "at_sea_cruising")],
    )
    vessel = _make_vessel(allowed_fuel_types=["VLSFO", "MGO"])
    flags = run_anomaly_checks(report, vessel)
    fuel_flags = [f for f in flags if f["rule"] == "fuel_type_mismatch"]
    assert len(fuel_flags) == 0


def test_fuel_type_skipped_when_no_profile():
    """Skip fuel type rule when vessel has no allowed_fuel_types."""
    report = _make_report(
        fuel_entries=[("UNKNOWN_FUEL", 1.0, "at_berth")],
    )
    vessel = _make_vessel(allowed_fuel_types=None)
    flags = run_anomaly_checks(report, vessel)
    fuel_flags = [f for f in flags if f["rule"] == "fuel_type_mismatch"]
    assert len(fuel_flags) == 0


def test_at_berth_consumption_ignored_for_distance_rule():
    """At-berth consumption does not affect consumption/distance check."""
    # Only at-sea consumption counts; 5 MT at sea over 100 NM is plausible
    report = _make_report(
        distance_nm=100.0,
        fuel_entries=[
            ("VLSFO", 5.0, "at_sea_cruising"),
            ("MGO", 10.0, "at_berth"),
        ],
    )
    flags = run_anomaly_checks(report, None)
    consumption_flags = [f for f in flags if f["rule"] == "consumption_vs_distance"]
    assert len(consumption_flags) == 0
