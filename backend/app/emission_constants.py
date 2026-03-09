"""
Emission factors for CO₂ calculation (tCO₂ per tonne fuel).

Reference: EU MRV Regulation Annex I, IMO Guidelines.
Used in formula: E = C × f (E = emissions MT, C = consumption MT, f = factor).
"""

# tCO₂ per tonne of fuel (tank-to-wake, default values)
EMISSION_FACTORS: dict[str, float] = {
    "VLSFO": 3.114,   # Very Low Sulfur Fuel Oil (EU MRV Annex I)
    "LSMGO": 3.151,   # Low Sulfur Marine Gas Oil (LFO)
    "MGO": 3.151,     # Marine Gas Oil
    "MDO": 3.151,     # Marine Diesel Oil
    "HFO": 3.114,     # Heavy Fuel Oil
    "LFO": 3.151,     # Light Fuel Oil
    "LNG": 2.75,      # Liquefied Natural Gas (typical, varies by engine)
    "biofuels": 2.0,  # Biofuels (typical blend; varies by feedstock)
    "other": 3.114,   # Fallback to VLSFO equivalent
}

DEFAULT_EMISSION_FACTOR = 3.114  # VLSFO default when fuel type unknown

# EU ETS Maritime applicability (phase-in 2024–2026)
# Fraction of CO₂ that requires EU Allowances by operational status
# Reference: EU ETS Maritime rules — 100% at EU port, 50% in EU waters
EU_ETS_APPLICABILITY: dict[str, float] = {
    "at_berth": 1.0,           # 100% — EU port (loading/unloading)
    "at_sea_cruising": 0.5,    # 50% — EU waters
    "at_anchor": 0.5,          # 50% — EU waters (simplified for MVP)
}
DEFAULT_EU_ETS_FACTOR = 0.5  # Fallback when operational status unknown

# Default carbon price for EUA cost estimation (EUR per EUA) — MVP; Task 9.4 will fetch live
DEFAULT_CARBON_PRICE_EUR = 80.0


def get_emission_factor(fuel_type: str) -> float:
    """Return emission factor for fuel type, or default if unknown."""
    normalized = fuel_type.upper().strip() if fuel_type else "other"
    return EMISSION_FACTORS.get(normalized, DEFAULT_EMISSION_FACTOR)


def get_eu_ets_factor(operational_status: str) -> float:
    """Return EU ETS applicability factor for operational status (0–1)."""
    normalized = (operational_status or "").lower().strip().replace(" ", "_")
    return EU_ETS_APPLICABILITY.get(normalized, DEFAULT_EU_ETS_FACTOR)
