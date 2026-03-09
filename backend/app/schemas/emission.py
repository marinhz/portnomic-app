"""Emission report schemas and LLM extraction JSON schema."""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# --- LLM Extraction Schema (contract for AI parser) ---

EXTRACTION_SCHEMA_VERSION = "1.0"

FUEL_TYPES = frozenset(
    {"VLSFO", "LSMGO", "MGO", "HFO", "LNG", "biofuels", "LFO", "MDO", "other"}
)
OPERATIONAL_STATUSES = frozenset({"at_sea_cruising", "at_berth", "at_anchor"})


class FuelEntryExtraction(BaseModel):
    """Single fuel entry as extracted by LLM from Noon/Bunker reports."""

    fuel_type: str = Field(
        ...,
        description="VLSFO|LSMGO|MGO|LNG|biofuels|HFO|LFO|MDO|other",
    )
    consumption_mt: float = Field(..., ge=0, description="Fuel consumed in metric tonnes")
    operational_status: str = Field(
        ...,
        description="at_sea_cruising|at_berth|at_anchor",
    )


class EmissionExtractionResult(BaseModel):
    """
    JSON schema for LLM extraction output.
    This is the contract between the AI parser and the calculation engine.
    """

    vessel_name: str = Field(..., description="Vessel name from report")
    imo_number: str = Field(..., description="IMO number (7 digits)")
    report_date: date = Field(..., description="Report date YYYY-MM-DD")
    fuel_entries: list[FuelEntryExtraction] = Field(
        default_factory=list,
        description="Fuel consumption entries",
    )
    distance_nm: float | None = Field(
        default=None,
        ge=0,
        description="Distance travelled in nautical miles (24h or since last port)",
    )


# --- API Schemas ---


class FuelEntryResponse(BaseModel):
    """Fuel entry in API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fuel_type: str
    consumption_mt: float
    operational_status: str


class EmissionReportCreate(BaseModel):
    """Create emission report (typically from AI extraction)."""

    vessel_id: uuid.UUID
    port_call_id: uuid.UUID | None = None
    email_id: uuid.UUID | None = None
    report_date: date
    fuel_entries: list[FuelEntryExtraction]
    distance_nm: float | None = None
    schema_version: str = EXTRACTION_SCHEMA_VERSION


class AnomalyFlag(BaseModel):
    """Single anomaly flag from AI Auditor."""

    rule: str = Field(..., description="Rule that triggered the flag")
    description: str = Field(..., description="Human-readable explanation")
    severity: str = Field(..., description="warning | error")


class EmissionReportResponse(BaseModel):
    """Emission report API response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    vessel_id: uuid.UUID
    port_call_id: uuid.UUID | None = None
    email_id: uuid.UUID | None = None
    report_date: date
    distance_nm: float | None = None
    extracted_at: datetime
    schema_version: str
    status: str = Field(
        default="verified",
        description="verified | flagged | failed — flagged when anomalies detected",
    )
    anomaly_flags: list[AnomalyFlag] | None = Field(
        default=None,
        description="List of anomaly flags from AI Auditor",
    )
    created_at: datetime
    updated_at: datetime | None = None
    fuel_entries: list[FuelEntryResponse] = Field(default_factory=list)


# --- C-Engine result schemas ---


class FuelBreakdown(BaseModel):
    """CO₂ breakdown per fuel type."""

    fuel_type: str = Field(..., description="Fuel type (e.g. VLSFO, MGO)")
    consumption_mt: float = Field(..., ge=0, description="Fuel consumed in metric tonnes")
    emission_factor: float = Field(..., ge=0, description="tCO₂ per tonne fuel used")
    co2_mt: float = Field(..., ge=0, description="CO₂ emissions in metric tonnes")


class EmissionsResult(BaseModel):
    """Result of CO₂ calculation for an emission report."""

    total_co2_mt: float = Field(..., ge=0, description="Total CO₂ emissions in metric tonnes")
    per_fuel_breakdown: list[FuelBreakdown] = Field(
        default_factory=list,
        description="Breakdown by fuel type with formula E = C × f",
    )


class EUAEstimate(BaseModel):
    """EU ETS allowance estimate for a voyage segment."""

    eua_count: float = Field(..., ge=0, description="Number of EU Allowances required")
    cost_eur: float = Field(..., ge=0, description="Estimated cost in EUR at given carbon price")
    carbon_price_eur: float = Field(..., ge=0, description="Carbon price used (EUR per EUA)")


class EmissionReportListResponse(BaseModel):
    """Emission report list item for dashboard."""

    id: uuid.UUID
    vessel_id: uuid.UUID
    vessel_name: str | None = None
    voyage_id: uuid.UUID | None = None
    report_date: date
    co2_mt: float
    eua_estimate_eur: float | None = None
    compliance_status: str = Field(
        default="green",
        description="green | yellow | red — FuelEU intensity target",
    )
    verification_status: str = Field(
        default="verified",
        description="verified | flagged | pending",
    )
    source_email_id: uuid.UUID | None = None
    created_at: datetime


class EmissionsSummaryResponse(BaseModel):
    """Aggregated emissions summary for dashboard."""

    total_co2_mt: float
    total_eua_estimate_eur: float | None = None
    voyage_count: int
    compliance: dict[str, int] = Field(
        default_factory=lambda: {"green": 0, "yellow": 0, "red": 0},
        description="Count of reports by compliance status",
    )


class EmissionReportDetailResponse(BaseModel):
    """Emission report detail for dashboard (includes computed co2, eua, fuel_breakdown)."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    vessel_id: uuid.UUID
    vessel_name: str | None = None
    vessel_imo: str | None = None
    voyage_id: uuid.UUID | None = None
    report_date: date
    co2_mt: float
    eua_estimate_eur: float | None = None
    compliance_status: str = "green"
    verification_status: str = "verified"
    fuel_breakdown: list[dict[str, Any]] = Field(
        default_factory=list,
        description="[{fuel_type, consumption_mt, co2_mt}]",
    )
    anomaly_flags: list[dict[str, str]] = Field(
        default_factory=list,
        description="[{code, message}]",
    )
    source_email_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None


class EmissionReportOverride(BaseModel):
    """Request to override anomaly flags after user review."""

    override: bool = Field(
        True,
        description="Set to true to mark report as verified and clear anomaly flags",
    )


class EmissionsCalculateRequest(BaseModel):
    """Request body for on-demand emissions calculation."""

    fuel_entries: list[FuelEntryExtraction] = Field(
        ...,
        description="Fuel consumption entries to calculate",
    )
    carbon_price_eur: float | None = Field(
        default=None,
        ge=0,
        description="Carbon price in EUR per EUA; if omitted, uses live price from API/cache/fallback",
    )


class EmissionsCalculateResponse(BaseModel):
    """Response for on-demand emissions calculation."""

    emissions: EmissionsResult
    eua_estimate: EUAEstimate
