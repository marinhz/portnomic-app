"""
Anomaly Detection (AI Auditor) for emission reports.

Flags reports where:
1. Consumption is physically impossible for the distance covered (at-sea segments).
2. Fuel types mentioned do not match the vessel's technical profile.

Prevents submission of fraudulent or erroneous data to authorities.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emission_report import (
    EmissionReport,
    REPORT_STATUS_FLAGGED,
    REPORT_STATUS_VERIFIED,
)
from app.models.vessel import Vessel

# Consumption (MT) / distance (NM) typical band for large vessels (industry benchmark).
# Outside 0.01–0.1 suggests implausible data. Flag if >2× or <0.2× expected.
CONSUMPTION_DISTANCE_MIN = 0.01
CONSUMPTION_DISTANCE_MAX = 0.1
OUTLIER_HIGH_MULTIPLIER = 2.0
OUTLIER_LOW_MULTIPLIER = 0.2

AT_SEA_STATUS = "at_sea_cruising"


def _check_consumption_vs_distance(
    distance_nm: float | None,
    at_sea_consumption_mt: float,
) -> dict[str, Any] | None:
    """Rule 1: Flag if consumption/distance ratio is outside plausible range.

    Only applies when we have at-sea consumption and distance.
    """
    if distance_nm is None or distance_nm <= 0 or at_sea_consumption_mt <= 0:
        return None

    ratio = at_sea_consumption_mt / distance_nm
    expected_min = CONSUMPTION_DISTANCE_MIN * OUTLIER_LOW_MULTIPLIER
    expected_max = CONSUMPTION_DISTANCE_MAX * OUTLIER_HIGH_MULTIPLIER

    if ratio > expected_max:
        return {
            "rule": "consumption_vs_distance",
            "description": (
                f"Consumption/distance ratio {ratio:.4f} MT/NM exceeds plausible "
                f"maximum ({expected_max:.4f}). Reported consumption may be too high "
                "for distance covered."
            ),
            "severity": "warning",
        }
    if ratio < expected_min:
        return {
            "rule": "consumption_vs_distance",
            "description": (
                f"Consumption/distance ratio {ratio:.4f} MT/NM is below plausible "
                f"minimum ({expected_min:.4f}). Reported consumption may be too low "
                "for distance covered."
            ),
            "severity": "warning",
        }
    return None


def _check_fuel_type_vs_profile(
    reported_fuel_types: set[str],
    allowed_fuel_types: list[str] | None,
) -> dict[str, Any] | None:
    """Rule 2: Flag if reported fuel types are not in vessel's allowed set.

    Skip when no vessel profile (allowed_fuel_types is None or empty).
    """
    if not allowed_fuel_types:
        return None

    allowed = {ft.upper().strip() for ft in allowed_fuel_types if ft}
    reported_normalized = {ft.upper().strip() for ft in reported_fuel_types if ft}

    unknown = reported_normalized - allowed
    if unknown:
        return {
            "rule": "fuel_type_mismatch",
            "description": (
                f"Reported fuel type(s) {sorted(unknown)} not in vessel's technical "
                f"profile (allowed: {sorted(allowed)})."
            ),
            "severity": "warning",
        }
    return None


def run_anomaly_checks(
    report: EmissionReport,
    vessel: Vessel | None,
) -> list[dict[str, Any]]:
    """Run all anomaly rules and return list of flags.

    Pure function; does not modify report. Caller persists results.
    """
    flags: list[dict[str, Any]] = []

    # Rule 1: Consumption vs distance (at-sea segments only)
    at_sea_consumption = sum(
        float(e.consumption_mt)
        for e in report.fuel_entries
        if (e.operational_status or "").lower().strip().replace(" ", "_") == AT_SEA_STATUS
    )
    total_consumption = sum(float(e.consumption_mt) for e in report.fuel_entries)
    flag1 = _check_consumption_vs_distance(
        distance_nm=report.distance_nm,
        at_sea_consumption_mt=at_sea_consumption,
    )
    if flag1:
        flags.append(flag1)

    # Rule 2: Fuel type vs vessel profile
    reported_fuel_types = {e.fuel_type for e in report.fuel_entries}
    flag2 = _check_fuel_type_vs_profile(
        reported_fuel_types=reported_fuel_types,
        allowed_fuel_types=vessel.allowed_fuel_types if vessel else None,
    )
    if flag2:
        flags.append(flag2)

    return flags


async def detect_and_apply_anomalies(
    db: AsyncSession,
    report: EmissionReport,
) -> None:
    """Run anomaly detection and update report with flags and status.

    Loads vessel with allowed_fuel_types. Sets report.anomaly_flags and report.status.
    """
    vessel = await db.get(Vessel, report.vessel_id)
    flags = run_anomaly_checks(report, vessel)

    report.anomaly_flags = flags if flags else None
    report.status = REPORT_STATUS_FLAGGED if flags else REPORT_STATUS_VERIFIED


__all__ = [
    "run_anomaly_checks",
    "detect_and_apply_anomalies",
]
