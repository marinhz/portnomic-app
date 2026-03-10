"""Detect report type (noon/bunker vs port-call) from email subject and body."""

import re

# Keywords that indicate Noon Report or Bunker Report
NOON_BUNKER_KEYWORDS = (
    "noon report",
    "bunker report",
    "daily report",
    "noon position",
    "noon data",
    "fuel consumption",
    "bunker delivery",
    "rob report",  # Remaining On Board
    "noon statement",
)


def is_emission_report(subject: str | None, body_text: str | None, body_html: str | None) -> bool:
    """Return True if email appears to be a Noon Report or Bunker Report."""
    combined = " ".join(filter(None, [subject or "", body_text or "", body_html or ""])).lower()
    if not combined.strip():
        return False
    for keyword in NOON_BUNKER_KEYWORDS:
        if keyword in combined:
            return True
    # Also check for common patterns like "Noon Report - VESSEL NAME"
    if re.search(r"\bnoon\s+report\b", combined, re.IGNORECASE):
        return True
    if re.search(r"\bbunker\s+(report|statement|delivery)\b", combined, re.IGNORECASE):
        return True
    return False


__all__ = ["is_emission_report"]
