"""Versioned prompt templates and output schemas for maritime email parsing."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_prompt_override import ParserType, TenantPromptOverride

CURRENT_VERSION = "v1"

PROMPTS: dict[str, str] = {
    "v1": """\
You are a maritime operations AI assistant. Your task is to extract structured data from operational emails related to port calls, vessel disbursement accounts, and maritime services.

Analyze the email and extract the following information into a JSON object:

Required fields:
- vessel_name: The name of the vessel (string or null)
- vessel_imo: The IMO number of the vessel if mentioned (string or null)
- port_name: The port name (string or null)
- port_code: The UN/LOCODE port code if mentioned (string or null)
- eta: Expected time of arrival in ISO 8601 format (string or null)
- etd: Expected time of departure in ISO 8601 format (string or null)
- line_items: Array of expense/service line items, each with:
  - description: What the charge is for (string, required)
  - amount: The monetary amount (number, required)
  - currency: Three-letter currency code, default "USD" (string)
  - quantity: Number of units if applicable (number or null)
  - unit_price: Price per unit if applicable (number or null)
  - service_date: Date/time of service in ISO 8601 format if stated (string or null)
- total_amount: Sum of all line item amounts (number or null)
- currency: Primary currency used in the document (string or null)
- summary: Brief one-sentence summary of the email content (string or null)

If a field cannot be determined from the email, set it to null.
For line_items, return an empty array [] if no expense items are found.
Always return valid JSON matching this exact schema.
""",
}

EMISSION_PROMPT_VERSION = "emission_v1"
EMISSION_DEFAULT_PROMPT = """\
You are a maritime emissions compliance AI. Extract structured fuel and voyage data from Captain's Noon Reports or Bunker Reports for EU ETS and FuelEU Maritime compliance.

Analyze the report and extract the following into a JSON object:

Required fields:
- vessel_name: The name of the vessel (string)
- imo_number: The IMO number (7 digits, string). If not found, use "UNKNOWN".
- report_date: The report date in YYYY-MM-DD format (string)
- fuel_entries: Array of fuel consumption entries, each with:
  - fuel_type: One of VLSFO, LSMGO, MGO, HFO, LNG, biofuels, LFO, MDO, other (normalize abbreviations)
  - consumption_mt: Fuel consumed in metric tonnes (number, >= 0)
  - operational_status: One of at_sea_cruising, at_berth, at_anchor
    (at_sea_cruising = cruising/underway, at_berth = loading/unloading in port, at_anchor = waiting at anchor)
- distance_nm: Distance travelled in nautical miles in the reporting period (number or null if not stated)

If no fuel entries are found, return fuel_entries: [].
Always return valid JSON matching this exact schema.
"""

# Leakage detector validation prompt — compares extracted data against operational context
LEAKAGE_VALIDATION_VERSION = "leakage_v1"
LEAKAGE_VALIDATION_PROMPT = """\
You are an audit assistant for maritime disbursement accounts. Compare the extracted invoice line items against the provided operational context (PortCall dates, existing DA line items) and return a JSON object with rule results.

Input: Extracted line items (with service_date, description, amount, quantity) and operational context (vessel stay window: eta/etd, existing line items in same port call).

Return JSON:
{
  "ld001_results": [{"line_item_ref": "description or index", "pass": true/false, "reason": "brief explanation"}],
  "ld002_results": [{"line_item_ref": "...", "pass": true/false, "reason": "..."}],
  "ld003_results": [{"line_item_ref": "...", "pass": true/false, "reason": "..."}]
}

Rules:
- LD-001: Service date must fall within vessel stay (eta to etd). Fail if outside.
- LD-002: No duplicate line items (same description + amount) in same port call. Fail if duplicate found.
- LD-003: If description mentions "Weekend" or "Holiday" rate, service_date must be weekend/holiday. Fail if weekday.
"""

DEFAULT_PROMPTS: dict[str, tuple[str, str]] = {
    ParserType.DA_EMAIL.value: (PROMPTS["v1"], CURRENT_VERSION),
    ParserType.EMISSION_REPORT.value: (EMISSION_DEFAULT_PROMPT, EMISSION_PROMPT_VERSION),
}


async def get_prompt(
    parser_type: str,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
    *,
    version: str | None = None,
) -> tuple[str, str]:
    """Return (prompt_text, version) for the parser type.

    When tenant_id and db are provided, checks TenantPromptOverride first.
    Otherwise uses default from prompts.py for the parser type.
    """
    if db and tenant_id:
        stmt = select(TenantPromptOverride).where(
            TenantPromptOverride.tenant_id == tenant_id,
            TenantPromptOverride.parser_type == parser_type,
        )
        result = await db.execute(stmt)
        override = result.scalar_one_or_none()
        if override is not None:
            return override.prompt_text, override.version

    default = DEFAULT_PROMPTS.get(parser_type)
    if default is not None:
        return default

    # Legacy: version-based lookup for da_email
    ver = version or CURRENT_VERSION
    prompt = PROMPTS.get(ver)
    if prompt is not None:
        return prompt, ver
    raise ValueError(f"Unknown prompt version or parser type: {parser_type!r} / {ver}")
