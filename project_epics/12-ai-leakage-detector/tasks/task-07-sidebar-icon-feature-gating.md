# Task 12.7 — Sidebar Icon & Feature Gating (Starter: Icon Only)

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev** and **tailwind-design-system** skills.

---

## Objective

Add the Leakage Detector to the sidebar navigation. Starter plans see the icon only (disabled/teaser); Professional and Enterprise plans get full access. Clicking the icon when on Starter shows an upgrade CTA.

---

## Scope

### 1. Sidebar icon

- Add Leakage Detector nav item (icon + label) to the sidebar.
- Icon visible to all plans (Starter, Professional, Enterprise).

### 2. Feature gating

- **Starter:** Icon is disabled or non-navigable; tooltip or badge indicates "Premium feature".
- **Professional / Enterprise:** Icon links to Leakage Detector route; full access.
- **On click (Starter):** Show upgrade CTA (modal, toast, or redirect to billing/upgrade page).

### 3. Backend

- Feature gate: `leakage_detector` (or equivalent) gated to Professional/Enterprise in limits/feature service.
- API: Return `leakage_detector_enabled: boolean` in tenant/subscription context for frontend to gate UI.

---

## Acceptance criteria

- [ ] Leakage Detector icon appears in sidebar for all plans.
- [ ] Starter: icon disabled; click shows upgrade CTA.
- [ ] Professional/Enterprise: icon navigates to Leakage Detector; full feature access.
- [ ] Backend feature gate enforced; frontend respects plan from subscription context.

---

## Related code

- `frontend/` — Sidebar/navigation component
- Epic 8 — Limits & feature gating, plan tiers, billing
- Epic 8 Task 8.4 — Limits & feature gating service

---

## Dependencies

- Epic 8 (Business & monetization) — Plan tiers, feature gating, limits service
