# Task 14.2 — TimelineEvent Model & Normalization

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Create a unified `TimelineEvent` model and normalization layer that maps data from DA line items, SOF timestamps, Noon Reports, and AIS data into a common structure for cross-reference.

---

## Scope

### 1. TimelineEvent model (Pydantic / domain)

| Field | Type | Notes |
|-------|------|-------|
| `source` | enum | `da`, `sof`, `noon_report`, `ais` |
| `source_document_id` | UUID | FK to Email or other source |
| `start` | datetime | Event start (timezone-aware) |
| `end` | datetime, nullable | Event end; null for point-in-time |
| `event_type` | str | e.g. `tug_service`, `pilot_on`, `berth_arrival`, `fuel_consumption`, `idle_at_anchorage` |
| `raw_data` | dict | Source-specific payload for traceability |
| `port_call_id` | UUID | Context |

### 2. Normalizers

- **DA normalizer:** Extract line items (tug hours, pilot hours, berth days) from DA/ai_raw_output → `TimelineEvent[]`.
- **SOF normalizer:** Parse SOF timestamps (Tug fast/off, Pilot on/off, Idle at Anchorage) → `TimelineEvent[]`.
- **Noon Report normalizer:** Fuel consumption, engine hours, position → `TimelineEvent[]`.
- **AIS normalizer:** Berth arrival/departure (placeholder until Task 14.5) → `TimelineEvent[]`.

### 3. Aggregator

- `get_timeline_events(port_call_id)` — Fetches all sources, normalizes, returns unified `List[TimelineEvent]` sorted by `start`.

---

## Acceptance criteria

- [ ] TimelineEvent model defined with all required fields.
- [ ] DA, SOF, Noon Report normalizers produce valid TimelineEvents.
- [ ] AIS normalizer stub (or placeholder) for Task 14.5 integration.
- [ ] `get_timeline_events(port_call_id)` returns merged, sorted events.

---

## Related code

- `backend/app/services/sentinel/` — TimelineEvent, normalizers
- Epic 3 — DA, PortCall
- Epic 9 — Noon Report / Emission data

---

## Dependencies

- Task 14.1 — time_overlap (used by downstream rules)
- Epic 3 — DA entity, line items
- Epic 9 — EmissionReport / Noon data
