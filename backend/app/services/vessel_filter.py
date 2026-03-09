"""Vessel-related email filter for sync-time filtering.

Implements Option C (hybrid): tenant vessels + heuristic fallback.
If tenant has vessels, match subject/body against vessel names and IMO.
If no vessels or no match, use maritime keyword heuristic.
"""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vessel import Vessel

# Maritime keywords for heuristic fallback when tenant has no vessels
MARITIME_KEYWORDS = [
    r"\bETA\b",
    r"\bETD\b",
    r"\bport\s+call\b",
    r"\bdisbursement",
    r"\bvessel\b",
    r"\bIMO\b",
    r"\barrival\b",
    r"\bdeparture\b",
    r"\bberth\b",
    r"\banchorage\b",
    r"\bloading\b",
    r"\bdischarge\b",
    r"\bcargo\b",
    r"\bport\b",
    r"\bdisbursement\s+account\b",
    r"\bport\s+agent\b",
    r"\bproforma\b",
    r"\bstatement\s+of\s+account\b",
]
MARITIME_PATTERN = re.compile("|".join(MARITIME_KEYWORDS), re.IGNORECASE)


async def get_tenant_vessel_terms(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[tuple[str | None, str | None]]:
    """Return list of (name, imo) for tenant vessels. Used for pattern matching."""
    stmt = select(Vessel.name, Vessel.imo).where(Vessel.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return [(r.name, r.imo) for r in result.all()]


def _matches_vessel_terms(
    text: str, vessel_terms: list[tuple[str | None, str | None]]
) -> bool:
    """Check if text contains any vessel name or IMO."""
    if not text:
        return False
    text_lower = text.lower()
    for name, imo in vessel_terms:
        if name and len(name) >= 3 and name.lower() in text_lower:
            return True
        if imo and imo in text:
            return True
    return False


def _matches_maritime_heuristic(text: str) -> bool:
    """Check if text contains maritime keywords."""
    if not text:
        return False
    return bool(MARITIME_PATTERN.search(text))


def is_vessel_related_email(
    subject: str | None,
    body_text: str | None,
    body_html: str | None,
    vessel_terms: list[tuple[str | None, str | None]],
) -> bool:
    """Return True if email appears vessel-related (Option C: hybrid).

    - If tenant has vessels: match against vessel names and IMO.
    - If no vessels or no match: use maritime keyword heuristic.
    """
    combined = " ".join(
        filter(None, [subject or "", body_text or "", body_html or ""])
    )
    if not combined.strip():
        return False

    if vessel_terms and _matches_vessel_terms(combined, vessel_terms):
        return True
    return _matches_maritime_heuristic(combined)
