# Task 14.5 — AIS Integration (aisstream.io)

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Integrate aisstream.io API to fetch actual berth arrival and departure times from AIS satellite data. This provides independent verification for Rule 2 (Berthage/Stay Verification).

---

## Scope

### 1. AIS client

- **Provider:** aisstream.io
- **Purpose:** Retrieve vessel "at berth" status and berth stay duration for a given port call.
- **Config:** API key / credentials via environment or tenant config (consider tenant-specific keys if supported).
- **Error handling:** Graceful degradation if AIS unavailable; Sentinel can run without AIS (Rules 1, 3 still active).

### 2. AIS normalizer integration

- Consume AIS response; produce `TimelineEvent[]` with `event_type` e.g. `berth_arrival`, `berth_departure`.
- Feed into `get_timeline_events` for Rule S-002.
- Cache or rate-limit AIS calls to respect provider limits.

### 3. Berth stay duration

- Compute `AIS_Berth_Stay_Duration` (days or hours) from berth_arrival to berth_departure.
- Expose for AuditEngine S-002 comparison with `DA_Berth_Fee_Days`.

---

## Acceptance criteria

- [ ] AIS client connects to aisstream.io; retrieves vessel position/berth data.
- [ ] AIS normalizer produces TimelineEvents for berth arrival/departure.
- [ ] AuditEngine S-002 can compare DA berth days vs. AIS berth stay duration.
- [ ] Failure to fetch AIS does not block other Sentinel rules.

---

## Related code

- `backend/app/services/sentinel/ais_client.py`
- `backend/app/services/sentinel/timeline_events.py` — AIS normalizer
- `backend/app/config.py` — AIS API key config

---

## Dependencies

- Task 14.2 — TimelineEvent, AIS normalizer placeholder
- aisstream.io API documentation
- Epic 3 — PortCall (vessel, port, dates for AIS lookup)
