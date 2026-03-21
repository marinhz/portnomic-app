"""TimelineEvent model — unified structure for DA, SOF, Noon Report, AIS events."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventSource(str, Enum):
    """Source system for the timeline event."""

    DA = "da"
    SOF = "sof"
    NOON_REPORT = "noon_report"
    AIS = "ais"


class TimelineEvent(BaseModel):
    """
    Unified event model for cross-referencing DA, SOF, Noon Report, and AIS data.
    Used by the Sentinel Triple-Check algorithm for temporal validation.
    """

    model_config = ConfigDict(frozen=True)

    source: EventSource = Field(..., description="Source: da, sof, noon_report, ais")
    source_document_id: uuid.UUID = Field(
        ..., description="FK to Email, DA, EmissionReport, or other source"
    )
    start: datetime = Field(..., description="Event start (timezone-aware)")
    end: datetime | None = Field(
        default=None,
        description="Event end; null for point-in-time events",
    )
    event_type: str = Field(
        ...,
        description="e.g. tug_service, pilot_on, berth_arrival, fuel_consumption, idle_at_anchorage",
    )
    raw_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific payload for traceability",
    )
    port_call_id: uuid.UUID = Field(..., description="Port call context")
