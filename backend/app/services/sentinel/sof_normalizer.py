"""SOF normalizer — parses SOF timestamps (Tug fast/off, Pilot on/off, Idle at Anchorage) → TimelineEvent[]."""

import uuid
from typing import Any

from app.services.sentinel._parse_utils import parse_datetime
from app.services.sentinel.models import EventSource, TimelineEvent

# Expected keys in SOF ai_raw_output or port_log dict
# Convention: parser outputs sof_timestamps or port_log with these fields
SOF_KEYS = {
    "tug_fast": "tug_service",  # start of tug
    "tug_off": "tug_service",   # end of tug
    "pilot_on": "pilot_on",
    "pilot_off": "pilot_off",
    "idle_at_anchorage_start": "idle_at_anchorage",
    "idle_at_anchorage_end": "idle_at_anchorage",
}


def normalize_sof(
    *,
    sof_data: dict[str, Any],
    source_document_id: uuid.UUID,
    port_call_id: uuid.UUID,
) -> list[TimelineEvent]:
    """
    Parse SOF timestamps into TimelineEvents.

    Expects sof_data with keys like:
    - tug_fast, tug_off (ISO datetime strings)
    - pilot_on, pilot_off
    - idle_at_anchorage_start, idle_at_anchorage_end

    For pairs (tug_fast/tug_off, pilot_on/pilot_off): creates one event with start/end.
    For single timestamps: creates point-in-time event (end=None).
    """
    events: list[TimelineEvent] = []

    # Pair (start_key, end_key) -> event_type
    pairs = [
        (("tug_fast", "tug_off"), "tug_service"),
        (("pilot_on", "pilot_off"), "pilot_service"),
        (("idle_at_anchorage_start", "idle_at_anchorage_end"), "idle_at_anchorage"),
    ]

    for (start_key, end_key), event_type in pairs:
        start_val = sof_data.get(start_key)
        end_val = sof_data.get(end_key)
        start_dt = parse_datetime(str(start_val)) if start_val else None
        end_dt = parse_datetime(str(end_val)) if end_val else None

        if start_dt:
            events.append(
                TimelineEvent(
                    source=EventSource.SOF,
                    source_document_id=source_document_id,
                    start=start_dt,
                    end=end_dt,
                    event_type=event_type,
                    raw_data={
                        start_key: start_val,
                        end_key: end_val,
                        **{k: v for k, v in sof_data.items() if k in (start_key, end_key)},
                    },
                    port_call_id=port_call_id,
                )
            )

    return events
