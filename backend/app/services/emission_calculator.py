"""
Calculation Engine (C-Engine): CO₂ emissions and EU ETS financial impact.

Formula: E = C × f (E = emissions MT, C = consumption MT, f = emission factor)
Emission factors from app.emission_constants (EU MRV Annex I).
EU ETS applicability from operational status (100% at berth, 50% EU waters).
"""

from typing import Protocol

from app.emission_constants import get_emission_factor, get_eu_ets_factor
from app.schemas.emission import EUAEstimate, EmissionsResult, FuelBreakdown


class ReportLike(Protocol):
    """Protocol for report-like objects with fuel entries (EmissionReport, EmissionExtractionResult)."""

    fuel_entries: list


def calculate_emissions(report: ReportLike) -> EmissionsResult:
    """Calculate CO₂ emissions from fuel consumption.

    For each fuel entry: E = consumption_mt × emission_factor.
    Aggregates total CO₂ and per-fuel breakdown.
    Deterministic and auditable (formula + factors in emission_constants).
    """
    breakdown: list[FuelBreakdown] = []
    total_co2_mt = 0.0

    for entry in report.fuel_entries:
        consumption_mt = float(entry.consumption_mt)
        factor = get_emission_factor(entry.fuel_type)
        co2_mt = consumption_mt * factor
        total_co2_mt += co2_mt
        breakdown.append(
            FuelBreakdown(
                fuel_type=entry.fuel_type,
                consumption_mt=consumption_mt,
                emission_factor=factor,
                co2_mt=co2_mt,
            )
        )

    return EmissionsResult(
        total_co2_mt=round(total_co2_mt, 6),
        per_fuel_breakdown=breakdown,
    )


def estimate_eua(report: ReportLike, carbon_price_eur: float) -> EUAEstimate:
    """Estimate EU Allowances required and cost for the voyage segment.

    EUAs ≈ CO₂ (t) × applicability factor (100% at berth, 50% EU waters).
    Cost = EUA count × carbon_price_eur.
    """
    if carbon_price_eur < 0:
        carbon_price_eur = 0.0

    eua_count = 0.0
    for entry in report.fuel_entries:
        consumption_mt = float(entry.consumption_mt)
        factor = get_emission_factor(entry.fuel_type)
        applicability = get_eu_ets_factor(entry.operational_status)
        co2_mt = consumption_mt * factor
        eua_count += co2_mt * applicability

    cost_eur = eua_count * carbon_price_eur
    return EUAEstimate(
        eua_count=round(eua_count, 6),
        cost_eur=round(cost_eur, 2),
        carbon_price_eur=carbon_price_eur,
    )


__all__ = ["calculate_emissions", "estimate_eua"]
