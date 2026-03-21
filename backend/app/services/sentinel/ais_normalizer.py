"""AIS normalizer — converts berth data from aisstream.io to TimelineEvent[]."""

import uuid
from typing import Any

from app.services.sentinel.ais_client import BerthData
from app.services.sentinel.models import EventSource, TimelineEvent


def normalize_ais(
    *,
    berth_data: BerthData | None = None,
    ais_data: dict[str, Any] | None = None,
    source_document_id: uuid.UUID | None = None,
    port_call_id: uuid.UUID,
) -> list[TimelineEvent]:
    """
    Convert AIS berth data to TimelineEvents for Rule S-002 (Berthage/Stay Verification).

    Produces berth_arrival and berth_departure events when BerthData is available.
    Falls back to empty list when AIS is unavailable; AuditEngine uses eta/etd stub.
    """
    events: list[TimelineEvent] = []

    # Primary: BerthData from ais_client
    if berth_data:
        doc_id = source_document_id or port_call_id
        events.append(
            TimelineEvent(
                source=EventSource.AIS,
                source_document_id=doc_id,
                start=berth_data.berth_arrival,
                end=berth_data.berth_departure,
                event_type="berth_arrival",
                raw_data={
                    "berth_arrival": berth_data.berth_arrival.isoformat(),
                    "berth_departure": berth_data.berth_departure.isoformat(),
                    "raw_positions_count": berth_data.raw_positions_count,
                },
                port_call_id=port_call_id,
            )
        )
        events.append(
            TimelineEvent(
                source=EventSource.AIS,
                source_document_id=doc_id,
                start=berth_data.berth_departure,
                end=None,
                event_type="berth_departure",
                raw_data={
                    "berth_departure": berth_data.berth_departure.isoformat(),
                    "raw_positions_count": berth_data.raw_positions_count,
                },
                port_call_id=port_call_id,
            )
        )

    # Legacy: raw ais_data dict (e.g. from tests or alternate sources)
    elif ais_data and isinstance(ais_data, dict):
        doc_id = source_document_id or port_call_id
        arr = ais_data.get("berth_arrival")
        dep = ais_data.get("berth_departure")
        if arr and dep:
            from datetime import datetime

            if isinstance(arr, str):
                arr = datetime.fromisoformat(arr.replace("Z", "+00:00"))
            if isinstance(dep, str):
                dep = datetime.fromisoformat(dep.replace("Z", "+00:00"))
            events.append(
                TimelineEvent(
                    source=EventSource.AIS,
                    source_document_id=doc_id,
                    start=arr,
                    end=dep,
                    event_type="berth_arrival",
                    raw_data=dict(ais_data),
                    port_call_id=port_call_id,
                )
            )
            events.append(
                TimelineEvent(
                    source=EventSource.AIS,
                    source_document_id=doc_id,
                    start=dep,
                    end=None,
                    event_type="berth_departure",
                    raw_data=dict(ais_data),
                    port_call_id=port_call_id,
                )
            )

    return events
