"""LLM-based parsing of Noon Reports and Bunker Reports for emission extraction."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant_prompt_override import ParserType
from app.schemas.emission import (
    EXTRACTION_SCHEMA_VERSION,
    FUEL_TYPES,
    OPERATIONAL_STATUSES,
    EmissionExtractionResult,
    FuelEntryExtraction,
)
from app.services.llm_client import call_llm
from app.services.prompts import EMISSION_PROMPT_VERSION, get_prompt

__all__ = ["parse_emission_content", "EMISSION_PROMPT_VERSION"]

logger = logging.getLogger("shipflow.emission_parser")


def _normalize_fuel_type(raw: str) -> str:
    """Normalize fuel type to schema enum. Returns 'other' if unknown."""
    normalized = raw.upper().strip() if raw else "other"
    if normalized in FUEL_TYPES:
        return normalized
    # Common mappings
    mapping = {
        "VLSFO": "VLSFO",
        "LSFO": "VLSFO",
        "LSMGO": "LSMGO",
        "MGO": "MGO",
        "MDO": "MDO",
        "HFO": "HFO",
        "LFO": "LFO",
        "LNG": "LNG",
        "BIOFUELS": "biofuels",
        "BIO": "biofuels",
    }
    return mapping.get(normalized, "other")


def _normalize_operational_status(raw: str) -> str:
    """Normalize operational status to schema enum."""
    normalized = (raw or "").lower().strip().replace(" ", "_")
    if normalized in OPERATIONAL_STATUSES:
        return normalized
    mapping = {
        "at_sea": "at_sea_cruising",
        "cruising": "at_sea_cruising",
        "underway": "at_sea_cruising",
        "at_berth": "at_berth",
        "berth": "at_berth",
        "loading": "at_berth",
        "unloading": "at_berth",
        "at_anchor": "at_anchor",
        "anchor": "at_anchor",
        "waiting": "at_anchor",
    }
    return mapping.get(normalized, "at_sea_cruising")


def _validate_and_normalize(raw: dict) -> EmissionExtractionResult:
    """Validate LLM output and normalize fuel/status values."""
    fuel_entries = raw.get("fuel_entries") or []
    normalized_entries = []
    for entry in fuel_entries:
        fe = dict(entry)
        fe["fuel_type"] = _normalize_fuel_type(fe.get("fuel_type", "other"))
        fe["operational_status"] = _normalize_operational_status(
            fe.get("operational_status", "at_sea_cruising")
        )
        normalized_entries.append(FuelEntryExtraction.model_validate(fe))
    raw["fuel_entries"] = [e.model_dump() for e in normalized_entries]
    return EmissionExtractionResult.model_validate(raw)


async def parse_emission_content(
    email_body: str,
    email_subject: str | None = None,
    *,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
) -> EmissionExtractionResult:
    """Parse Noon/Bunker report content using LLM and return validated emission extraction."""
    user_content = ""
    if email_subject:
        user_content += f"Subject: {email_subject}\n\n"
    user_content += email_body

    from app.config import settings

    max_chars = settings.llm_max_input_chars
    if len(user_content) > max_chars:
        original_len = len(user_content)
        user_content = user_content[:max_chars] + "\n\n[... truncated for token limit ...]"
        logger.info("Emission report truncated from %d to %d chars for LLM", original_len, max_chars)

    prompt_text, _ = await get_prompt(
        ParserType.EMISSION_REPORT.value, tenant_id=tenant_id, db=db
    )
    raw_result = await call_llm(
        prompt_text, user_content, tenant_id=tenant_id, db=db
    )
    return _validate_and_normalize(raw_result)
