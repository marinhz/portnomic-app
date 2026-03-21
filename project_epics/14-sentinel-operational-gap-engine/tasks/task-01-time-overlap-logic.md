# Task 14.1 — time_overlap Logic & Core Utilities

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Implement the foundational `time_overlap` logic that determines whether two events claimed to happen at the same time actually did. This is the **priority foundation** for all temporal validations in the Sentinel Triple-Check algorithm.

---

## Scope

### 1. time_overlap utility

- **Input:** Two time intervals: `(start_a, end_a)` and `(start_b, end_b)` (datetime or timestamp).
- **Output:** Boolean or overlap metadata (e.g. overlap duration, overlap type).
- **Edge cases:**
  - Partial overlap (one event starts before the other ends).
  - Full containment (one event entirely within the other).
  - Adjacent events (no gap vs. gap).
  - None/zero-duration events.
- **Optional buffer:** Support configurable buffer (e.g. 0.5hr) for "within tolerance" checks.

### 2. Time interval helpers

- `interval_contains(other)` — Is one interval fully contained in another?
- `interval_overlap_duration(a, b)` — Returns overlap duration in hours (or zero).
- `intervals_claimed_same_time(a, b, buffer_hours)` — High-level check for "claimed at same time" semantics.

### 3. Module location

- `backend/app/services/sentinel/time_overlap.py` or equivalent under `sentinel` package.
- Unit tests with explicit datetime fixtures.

---

## Acceptance criteria

- [ ] `time_overlap` correctly identifies when two intervals overlap.
- [ ] Edge cases (partial, full containment, adjacent, zero-duration) handled.
- [ ] Optional buffer parameter supported for Rule 1 (0.5hr tug buffer).
- [ ] Unit tests cover all overlap scenarios.
- [ ] No external dependencies; pure datetime logic.

---

## Related code

- `backend/app/services/sentinel/` — New package for Sentinel engine
- Epic 14 — All subsequent tasks depend on this

---

## Dependencies

- Epic 1 — Base project structure
- Python 3.11+ datetime handling
