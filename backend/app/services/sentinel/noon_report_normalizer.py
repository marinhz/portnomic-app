"""Noon Report normalizer — fuel consumption, engine hours, position → TimelineEvent[]."""

import uuid
from datetime import date, datetime, timezone

from app.services.sentinel.models import EventSource, TimelineEvent


def normalize_noon_report(
    *,
    report_id: uuid.UUID,
    port_call_id: uuid.UUID,
    report_date: date | datetime | str,
    fuel_entries: list[dict] | None = None,
    distance_nm: float | None = None,
    email_id: uuid.UUID | None = None,
) -> list[TimelineEvent]:
    """
    Extract timeline events from EmissionReport / Noon Report.

    - fuel_consumption: one event per fuel entry (point-in-time at report_date)
    - Maps operational_status at_anchor -> idle_at_anchorage for Rule 3
    """
    events: list[TimelineEvent] = []

    if isinstance(report_date, str):
        try:
            dt = datetime.fromisoformat(report_date.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    elif isinstance(report_date, date) and not isinstance(report_date, datetime):
        dt = datetime.combine(report_date, datetime.min.time(), tzinfo=timezone.utc)
    else:
        dt = report_date
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

    # Use report_id as source_document; EmissionReport is the canonical source
    source_doc_id = report_id

    if fuel_entries:
        for entry in fuel_entries:
            op_status = (entry.get("operational_status") or "").lower().replace(" ", "_")
            event_type = "idle_at_anchorage" if op_status == "at_anchor" else "fuel_consumption"

            events.append(
                TimelineEvent(
                    source=EventSource.NOON_REPORT,
                    source_document_id=source_doc_id,
                    start=dt,
                    end=None,
                    event_type=event_type,
                    raw_data={
                        "fuel_type": entry.get("fuel_type"),
                        "consumption_mt": entry.get("consumption_mt"),
                        "operational_status": op_status,
                    },
                    port_call_id=port_call_id,
                )
            )

    # Position / distance as optional point-in-time event
    if distance_nm is not None:
        events.append(
            TimelineEvent(
                source=EventSource.NOON_REPORT,
                source_document_id=source_doc_id,
                start=dt,
                end=None,
                event_type="position_update",
                raw_data={"distance_nm": distance_nm, "email_id": str(email_id) if email_id else None},
                port_call_id=port_call_id,
            )
        )

    return events
