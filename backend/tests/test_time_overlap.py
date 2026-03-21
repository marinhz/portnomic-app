"""Tests for Sentinel time_overlap logic — temporal validation foundation."""

from datetime import datetime, timedelta

import pytest

from app.services.sentinel.time_overlap import (
    Interval,
    interval_contains,
    interval_overlap_duration,
    intervals_claimed_same_time,
    time_overlap,
    time_overlap_detail,
)


# Fixtures: explicit datetime intervals for repeatable tests
T0 = datetime(2025, 3, 15, 10, 0, 0)
T1 = datetime(2025, 3, 15, 12, 0, 0)
T2 = datetime(2025, 3, 15, 14, 0, 0)
T3 = datetime(2025, 3, 15, 16, 0, 0)


# --- time_overlap core ---


def test_partial_overlap():
    """Partial overlap: one event starts before the other ends."""
    assert time_overlap(T0, T2, T1, T3) is True
    assert time_overlap(T1, T3, T0, T2) is True


def test_full_containment():
    """Full containment: one event entirely within the other."""
    assert time_overlap(T0, T3, T1, T2) is True
    assert time_overlap(T1, T2, T0, T3) is True


def test_adjacent_no_gap():
    """Adjacent events (touching): end_a == start_b — no overlap without buffer."""
    assert time_overlap(T0, T1, T1, T2) is False
    assert time_overlap(T1, T2, T0, T1) is False


def test_adjacent_with_buffer():
    """Adjacent events with buffer: within tolerance counts as overlap."""
    assert time_overlap(T0, T1, T1, T2, buffer_hours=0.5) is True


def test_adjacent_with_buffer_no_gap_bridged():
    """Small gap bridged by buffer."""
    half_hr = timedelta(hours=0.5)
    end_a = T1
    start_b = T1 + half_hr
    assert time_overlap(T0, end_a, start_b, T2, buffer_hours=0.5) is True


def test_no_overlap():
    """No overlap: clear gap between intervals."""
    assert time_overlap(T0, T1, T2, T3) is False
    assert time_overlap(T2, T3, T0, T1) is False


def test_zero_duration_contained():
    """Zero-duration event contained within another."""
    point = datetime(2025, 3, 15, 11, 0, 0)
    assert time_overlap(T0, T2, point, point) is True
    assert time_overlap(point, point, T0, T2) is True


def test_zero_duration_outside():
    """Zero-duration event outside other interval."""
    point = datetime(2025, 3, 15, 18, 0, 0)
    assert time_overlap(T0, T2, point, point) is False


def test_identical_intervals():
    """Identical intervals overlap."""
    assert time_overlap(T0, T2, T0, T2) is True


def test_buffer_with_gap():
    """Buffer allows intervals slightly apart to count as overlap."""
    half_hr = timedelta(hours=0.5)
    end_a = T1
    start_b = T1 + half_hr
    assert time_overlap(T0, end_a, start_b, T2, buffer_hours=0.5) is True


def test_buffer_insufficient():
    """Buffer too small for gap — no overlap."""
    one_hr = timedelta(hours=1)
    end_a = T1
    start_b = T1 + one_hr
    assert time_overlap(T0, end_a, start_b, T2, buffer_hours=0.5) is False


# --- time_overlap_detail ---


def test_detail_partial_overlap():
    """Detail returns correct metadata for partial overlap."""
    d = time_overlap_detail(T0, T2, T1, T3)
    assert d.overlaps is True
    assert d.overlap_type == "partial"
    assert d.overlap_duration_hours == pytest.approx(2.0)
    assert d.overlap_start == T1
    assert d.overlap_end == T2


def test_detail_full_containment():
    """Detail for full containment."""
    d = time_overlap_detail(T0, T3, T1, T2)
    assert d.overlaps is True
    assert d.overlap_type == "full_containment"
    assert d.overlap_duration_hours == pytest.approx(2.0)


def test_detail_adjacent():
    """Detail for adjacent (no overlap)."""
    d = time_overlap_detail(T0, T1, T1, T2)
    assert d.overlaps is False
    assert d.overlap_type == "adjacent"
    assert d.overlap_duration_hours == 0.0


def test_detail_none():
    """Detail for no overlap."""
    d = time_overlap_detail(T0, T1, T2, T3)
    assert d.overlaps is False
    assert d.overlap_type == "none"
    assert d.overlap_duration_hours == 0.0


# --- interval_contains ---


def test_interval_contains_inner_within_outer():
    """Inner fully contained in outer."""
    outer = Interval(T0, T3)
    inner = Interval(T1, T2)
    assert interval_contains(outer, inner) is True
    assert outer.contains(inner) is True


def test_interval_contains_not_contained():
    """Inner not fully contained."""
    outer = Interval(T1, T2)
    inner = Interval(T0, T3)
    assert interval_contains(outer, inner) is False


def test_interval_contains_tuple():
    """interval_contains works with tuples."""
    assert interval_contains((T0, T3), (T1, T2)) is True
    assert interval_contains((T1, T2), (T0, T3)) is False


def test_interval_contains_same():
    """Identical intervals: contained."""
    iv = Interval(T0, T2)
    assert interval_contains(iv, iv) is True


# --- interval_overlap_duration ---


def test_overlap_duration_positive():
    """Overlap duration in hours: T0-T2 (10–14) ∩ T1-T3 (12–16) = 2hr."""
    assert interval_overlap_duration(
        Interval(T0, T2), Interval(T1, T3)
    ) == pytest.approx(2.0)


def test_overlap_duration_zero():
    """No overlap returns 0."""
    assert interval_overlap_duration(
        Interval(T0, T1), Interval(T2, T3)
    ) == 0.0


def test_overlap_duration_tuple():
    """interval_overlap_duration works with tuples."""
    assert interval_overlap_duration((T0, T2), (T1, T3)) == pytest.approx(2.0)


# --- intervals_claimed_same_time ---


def test_claimed_same_time_overlap():
    """Overlapping intervals claimed same time."""
    assert intervals_claimed_same_time(
        Interval(T0, T2), Interval(T1, T3)
    ) is True


def test_claimed_same_time_adjacent_with_buffer():
    """Adjacent with buffer = claimed same time."""
    assert intervals_claimed_same_time(
        Interval(T0, T1), Interval(T1, T2), buffer_hours=0.5
    ) is True


def test_claimed_same_time_adjacent_no_buffer():
    """Adjacent without buffer = not claimed same time."""
    assert intervals_claimed_same_time(
        Interval(T0, T1), Interval(T1, T2)
    ) is False


def test_claimed_same_time_gap():
    """Gap = not claimed same time."""
    assert intervals_claimed_same_time(
        Interval(T0, T1), Interval(T2, T3)
    ) is False


# --- Interval class ---


def test_interval_duration_hours():
    """Interval.duration_hours."""
    iv = Interval(T0, T1)
    assert iv.duration_hours == pytest.approx(2.0)


def test_interval_zero_duration():
    """Zero-duration interval."""
    iv = Interval(T0, T0)
    assert iv.duration_hours == 0.0


def test_interval_invalid_start_after_end():
    """Interval rejects start > end."""
    with pytest.raises(ValueError, match="start.*must be <= end"):
        Interval(T2, T0)
