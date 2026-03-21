"""Shared parsing utilities for timeline normalizers."""

from datetime import datetime


def parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO 8601 date/time string; return None if invalid."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
