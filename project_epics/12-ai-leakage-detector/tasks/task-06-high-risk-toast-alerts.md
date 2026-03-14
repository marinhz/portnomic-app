# Task 12.6 — High-Risk Invoice Toast Alerts

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev** and **tailwind-design-system** skills.

---

## Objective

Use Sonner toasts to alert the agent of "High Risk" invoices immediately upon parsing. Trigger when anomalies with severity `high` or `critical` are detected.

---

## Scope

### 1. Trigger

- When parse result or DA load includes anomalies with severity `high` or `critical`.
- Can be triggered via:
  - Real-time: WebSocket or polling after parse job completes.
  - On navigation: When user opens DA workspace or email list for a high-risk invoice.

### 2. Toast content

- Title: "High Risk Invoice Detected"
- Description: Brief summary (e.g. "3 anomalies found (LD-001, LD-003)").
- Action: Link to DA or email detail for review.
- Style: Warning or error variant (Sonner).

### 3. Avoid spam

- Debounce or throttle: Don't show same invoice toast repeatedly.
- Use session/local state to track "already shown" for current session.

---

## Acceptance criteria

- [ ] Sonner toast appears when high/critical anomalies detected.
- [ ] Toast includes actionable link to DA or email.
- [ ] No duplicate toasts for same invoice in same session.

---

## Related code

- `frontend/` — DA workspace, email list, parse result views
- Sonner — toast component
- Epic 7 — UX polish (Sonner already in use)

---

## Dependencies

- Task 12.5 — Discrepancy UI (anomaly data available)
- Epic 7 — Sonner toasts
