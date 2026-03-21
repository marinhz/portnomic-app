"""
Time overlap logic — determines whether two events claimed at the same time actually did.

Core foundation for temporal validations in the Sentinel Triple-Check algorithm.
Handles partial overlap, full containment, adjacent events, zero-duration events,
and optional buffer for "within tolerance" checks (e.g. Rule 1: 0.5hr tug buffer).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

# Accept datetime or datetime-like (timestamp); use datetime for canonical logic
DatetimeLike = datetime


@dataclass(frozen=True)
class Interval:
    """Immutable time interval (start, end)."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start > self.end:
            msg = f"interval start {self.start} must be <= end {self.end}"
            raise ValueError(msg)

    def contains(self, other: "Interval") -> bool:
        """Whether this interval fully contains the other (other within self)."""
        return interval_contains(self, other)

    @property
    def duration_hours(self) -> float:
        """Duration in hours (0 for zero-duration interval)."""
        delta = self.end - self.start
        return delta.total_seconds() / 3600.0


OverlapType = Literal["partial", "full_containment", "adjacent", "none"]


@dataclass
class OverlapDetail:
    """Metadata about overlap between two intervals."""

    overlaps: bool
    overlap_type: OverlapType
    overlap_duration_hours: float
    overlap_start: datetime | None
    overlap_end: datetime | None


def _to_datetime(v: DatetimeLike) -> datetime:
    """Normalize to datetime (assume already datetime for now)."""
    if isinstance(v, datetime):
        return v
    raise TypeError(f"expected datetime, got {type(v)}")


def _ensure_interval(
    a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime
) -> None:
    """Validate that start <= end for both intervals."""
    if a_start > a_end:
        msg = f"interval A: start {a_start} must be <= end {a_end}"
        raise ValueError(msg)
    if b_start > b_end:
        msg = f"interval B: start {b_start} must be <= end {b_end}"
        raise ValueError(msg)


def time_overlap(
    start_a: DatetimeLike,
    end_a: DatetimeLike,
    start_b: DatetimeLike,
    end_b: DatetimeLike,
    buffer_hours: float = 0.0,
) -> bool:
    """
    Determine if two time intervals overlap (or are within buffer tolerance).

    Args:
        start_a, end_a: First interval (inclusive start, exclusive or inclusive end).
        start_b, end_b: Second interval.
        buffer_hours: Optional buffer (e.g. 0.5 for Rule 1 tug buffer).
                     Intervals with a gap up to this many hours are considered overlapping.

    Returns:
        True if intervals overlap (or are within buffer), False otherwise.

    Edge cases:
        - Partial overlap: one event starts before the other ends.
        - Full containment: one event entirely within the other.
        - Adjacent: end_a == start_b or end_b == start_a.
          With buffer_hours > 0, adjacent intervals may be considered overlapping.
        - Zero-duration: start == end; may overlap if contained in other.
    """
    detail = time_overlap_detail(start_a, end_a, start_b, end_b, buffer_hours)
    return detail.overlaps


def time_overlap_detail(
    start_a: DatetimeLike,
    end_a: DatetimeLike,
    start_b: DatetimeLike,
    end_b: DatetimeLike,
    buffer_hours: float = 0.0,
) -> OverlapDetail:
    """
    Return overlap metadata for two intervals.

    Args:
        start_a, end_a: First interval.
        start_b, end_b: Second interval.
        buffer_hours: Optional buffer for tolerance checks.

    Returns:
        OverlapDetail with overlaps, overlap_type, overlap_duration_hours, etc.
    """
    sa = _to_datetime(start_a)
    ea = _to_datetime(end_a)
    sb = _to_datetime(start_b)
    eb = _to_datetime(end_b)
    _ensure_interval(sa, ea, sb, eb)

    overlap_start = max(sa, sb)
    overlap_end = min(ea, eb)
    duration_sec = (overlap_end - overlap_start).total_seconds()
    duration_hours = max(0.0, duration_sec / 3600.0)

    if duration_sec > 0:
        overlaps = True
        if (sa <= sb and eb <= ea) or (sb <= sa and ea <= eb):
            overlap_type: OverlapType = "full_containment"
        else:
            overlap_type = "partial"
    elif duration_sec == 0:
        adjacent = ea == sb or eb == sa
        overlap_type = "adjacent"
        if adjacent:
            overlaps = buffer_hours > 0
        else:
            overlaps = True
    else:
        overlap_type = "none"
        gap_hours = (
            (sb - ea).total_seconds() / 3600.0
            if ea < sb
            else (sa - eb).total_seconds() / 3600.0
        )
        overlaps = buffer_hours > 0 and gap_hours <= buffer_hours

    return OverlapDetail(
        overlaps=overlaps,
        overlap_type=overlap_type,
        overlap_duration_hours=duration_hours,
        overlap_start=overlap_start if overlaps and duration_sec >= 0 else None,
        overlap_end=overlap_end if overlaps and duration_sec >= 0 else None,
    )


def interval_contains(outer: Interval | tuple[datetime, datetime], inner: Interval | tuple[datetime, datetime]) -> bool:
    """
    Whether one interval fully contains the other (inner within outer).

    Args:
        outer: The containing interval.
        inner: The interval that should be inside outer.

    Returns:
        True if inner is fully contained in outer (start and end within bounds).
    """
    o_start, o_end = _unwrap(outer)
    i_start, i_end = _unwrap(inner)
    _ensure_interval(o_start, o_end, i_start, i_end)
    return o_start <= i_start and i_end <= o_end


def _unwrap(interval: Interval | tuple[datetime, datetime]) -> tuple[datetime, datetime]:
    if isinstance(interval, Interval):
        return (interval.start, interval.end)
    return (interval[0], interval[1])


def interval_overlap_duration(
    a: Interval | tuple[datetime, datetime],
    b: Interval | tuple[datetime, datetime],
) -> float:
    """
    Return overlap duration in hours (0 if no overlap).

    Args:
        a: First interval.
        b: Second interval.

    Returns:
        Overlap duration in hours, or 0.0 if no overlap.
    """
    a_start, a_end = _unwrap(a)
    b_start, b_end = _unwrap(b)
    detail = time_overlap_detail(a_start, a_end, b_start, b_end, buffer_hours=0.0)
    return detail.overlap_duration_hours


def intervals_claimed_same_time(
    a: Interval | tuple[datetime, datetime],
    b: Interval | tuple[datetime, datetime],
    buffer_hours: float = 0.0,
) -> bool:
    """
    High-level check: are two intervals "claimed at the same time"?

    Uses overlap logic with optional buffer (e.g. 0.5hr for Rule 1 tug buffer).

    Args:
        a: First interval.
        b: Second interval.
        buffer_hours: Tolerance buffer in hours.

    Returns:
        True if intervals overlap or are within buffer of overlapping.
    """
    a_start, a_end = _unwrap(a)
    b_start, b_end = _unwrap(b)
    return time_overlap(a_start, a_end, b_start, b_end, buffer_hours)
