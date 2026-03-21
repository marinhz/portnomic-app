"""Sentinel Operational Gap Engine — temporal validation and audit utilities."""

from app.services.sentinel.audit_engine import AuditEngine, AuditReport
from app.services.sentinel.models import EventSource, TimelineEvent
from app.services.sentinel.time_overlap import (
    Interval,
    OverlapDetail,
    interval_contains,
    interval_overlap_duration,
    intervals_claimed_same_time,
    time_overlap,
    time_overlap_detail,
)
from app.services.sentinel.timeline_aggregator import get_timeline_events

__all__ = [
    "AuditEngine",
    "AuditReport",
    "EventSource",
    "Interval",
    "OverlapDetail",
    "TimelineEvent",
    "get_timeline_events",
    "interval_contains",
    "interval_overlap_duration",
    "intervals_claimed_same_time",
    "time_overlap",
    "time_overlap_detail",
]
