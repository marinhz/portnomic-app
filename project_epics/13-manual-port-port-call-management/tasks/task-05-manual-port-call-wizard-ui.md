# Task 13.5 — Manual Port Call Wizard UI

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

Implement a 3-step wizard at `/port-calls/new` for manual Port Call creation: Vessel → Port → ETA/ETD/Agent.

---

## Scope

- **Route:** `/port-calls/new` (may already exist; enhance to wizard flow).
- **Step 1:** Search/select Vessel (combobox or searchable select from vessels API).
- **Step 2:** Search/select Port (from Port Directory API).
- **Step 3:** ETA, ETD, Agent Assigned (text or user select).
- Submit creates PortCall via `POST /port-calls` with `source: "manual"`.
- Stepper UI (e.g. shadcn Stepper or numbered steps).

---

## Acceptance criteria

- [ ] Wizard guides user through Vessel → Port → ETA/ETD/Agent.
- [ ] Vessel and Port are searchable/selectable.
- [ ] Created PortCall has `source="manual"` and agent_assigned when provided.
- [ ] Success redirects to Port Call detail or list.
