"""DA normalizer — extracts line items from DisbursementAccount or ai_raw_output → TimelineEvent[]."""

import uuid
from datetime import timedelta
from typing import Any

from app.services.sentinel._parse_utils import parse_datetime
from app.services.sentinel.models import EventSource, TimelineEvent

# Keywords to map line item descriptions to event types
TUG_KEYWORDS = ("tug", "towing")
PILOT_KEYWORDS = ("pilot", "pilotage")
BERTH_KEYWORDS = ("berth", "berthage", "quay", "wharf", "mooring")


def _description_to_event_type(desc: str) -> str | None:
    """Map line item description to event_type."""
    lower = (desc or "").lower()
    if any(kw in lower for kw in TUG_KEYWORDS):
        return "tug_service"
    if any(kw in lower for kw in PILOT_KEYWORDS):
        return "pilot_service"
    if any(kw in lower for kw in BERTH_KEYWORDS):
        return "berth_fee_days"
    return None


def normalize_da_line_items(
    *,
    line_items: list[dict[str, Any]],
    source_document_id: uuid.UUID,
    port_call_id: uuid.UUID,
    eta: Any = None,
    etd: Any = None,
) -> list[TimelineEvent]:
    """
    Extract timeline events from DA line items (tug hours, pilot hours, berth days).

    Uses service_date when present; otherwise uses eta/etd for context.
    For per-hour items (tug, pilot): start from service_date or eta, end = start + quantity hours.
    For berth: start from eta, end from etd.
    """
    events: list[TimelineEvent] = []
    eta_dt = parse_datetime(str(eta)) if eta else None
    etd_dt = parse_datetime(str(etd)) if etd else None

    for li in line_items or []:
        event_type = _description_to_event_type(li.get("description") or "")
        if not event_type:
            continue

        service_date = parse_datetime(li.get("service_date"))
        quantity = li.get("quantity")
        try:
            qty = float(quantity) if quantity is not None else 1.0
        except (ValueError, TypeError):
            qty = 1.0

        start_dt = service_date or eta_dt or etd_dt
        if not start_dt:
            continue

        end_dt = None
        if event_type == "berth_fee_days":
            end_dt = etd_dt or (start_dt + timedelta(days=max(1.0, qty)))
        elif event_type in ("tug_service", "pilot_service"):
            end_dt = start_dt + timedelta(hours=max(0.0, qty))

        events.append(
            TimelineEvent(
                source=EventSource.DA,
                source_document_id=source_document_id,
                start=start_dt,
                end=end_dt,
                event_type=event_type,
                raw_data={
                    "description": li.get("description"),
                    "quantity": qty,
                    "amount": li.get("amount"),
                },
                port_call_id=port_call_id,
            )
        )

    return events
