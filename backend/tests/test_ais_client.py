"""Tests for AIS client helpers — Task 14.5."""

from datetime import datetime, timezone

import pytest

from app.services.sentinel.ais_client import (
    BerthData,
    _build_bounding_box,
    _infer_berth_from_positions,
    _parse_ais_timestamp,
)


def test_parse_ais_timestamp():
    """_parse_ais_timestamp parses aisstream Metadata time_utc format."""
    ts = _parse_ais_timestamp("2022-12-29 18:22:32.318353 +0000 UTC")
    assert ts is not None
    assert ts.year == 2022
    assert ts.month == 12
    assert ts.day == 29
    assert ts.hour == 18
    assert ts.minute == 22
    assert ts.second == 32
    assert ts.tzinfo == timezone.utc


def test_parse_ais_timestamp_none_returns_none():
    """_parse_ais_timestamp returns None for None or empty."""
    assert _parse_ais_timestamp(None) is None
    assert _parse_ais_timestamp("") is None


def test_build_bounding_box():
    """_build_bounding_box produces aisstream format."""
    bbox = _build_bounding_box(51.9, 4.5)
    assert len(bbox) == 1
    assert len(bbox[0]) == 2
    [[lat1, lon1], [lat2, lon2]] = bbox[0]
    assert lat1 < 51.9 < lat2
    assert lon1 < 4.5 < lon2


def test_infer_berth_from_positions_speed_below_threshold():
    """_infer_berth_from_positions infers berth when Sog < threshold."""
    t1 = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 10, 10, 0, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp": t1, "sog": 0.0},
        {"timestamp": t2, "sog": 0.2},
        {"timestamp": t3, "sog": 0.4},
    ]

    result = _infer_berth_from_positions(positions, speed_threshold_knots=0.5)

    assert result is not None
    assert result.berth_arrival == t1
    assert result.berth_departure == t3
    assert result.raw_positions_count == 3


def test_infer_berth_from_positions_ignores_high_speed():
    """Positions with Sog >= threshold are not counted as at berth."""
    t1 = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 10, 10, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp": t1, "sog": 1.5},
        {"timestamp": t2, "sog": 2.0},
    ]

    result = _infer_berth_from_positions(positions, speed_threshold_knots=0.5)

    assert result is None


def test_infer_berth_from_positions_insufficient_data():
    """Returns None when fewer than 2 at-berth positions."""
    t1 = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    positions = [{"timestamp": t1, "sog": 0.0}]

    result = _infer_berth_from_positions(positions, speed_threshold_knots=0.5)

    assert result is None


def test_infer_berth_from_positions_handles_missing_sog():
    """Positions without sog are skipped."""
    t1 = datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 3, 10, 10, 0, 0, tzinfo=timezone.utc)
    positions = [
        {"timestamp": t1},
        {"timestamp": t2, "sog": 0.0},
    ]

    result = _infer_berth_from_positions(positions, speed_threshold_knots=0.5)

    assert result is None


@pytest.mark.asyncio
async def test_fetch_berth_data_no_api_key_returns_none():
    """fetch_berth_data returns None when aisstream_api_key is empty (no DB needed)."""
    from unittest.mock import AsyncMock, patch

    from app.services.sentinel.ais_client import fetch_berth_data

    mock_db = AsyncMock()
    with patch("app.services.sentinel.ais_client.settings") as mock_settings:
        mock_settings.aisstream_api_key = ""
        result = await fetch_berth_data(mock_db, __import__("uuid").uuid4(), __import__("uuid").uuid4())

    assert result is None
    mock_db.execute.assert_not_called()
