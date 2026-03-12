# Task 8.10 — Plan Limits Restructure: Shift Limits Up One Tier

**Epic:** [08-business-monetization](../epic.md)

**Type:** Feature

---

## Objective

Restructure plan limits so that **Starter limits move to Professional** and **Professional limits move to Enterprise**. This creates a new tier structure with lower limits for Starter and shifts existing limits upward.

## Problem statement

- **Current limits:** Starter (3 users, 10 vessels, 50 DAs/month, 100 AI parses) → Professional (10, 50, 200, 500) → Enterprise (Unlimited).
- **Desired:** Starter limits → Professional; Professional limits → Enterprise.
- **Outcome:** New Starter tier needs lower limits; Professional and Enterprise get the shifted values.

## Proposed New Limits

| Plan | Users | Vessels | DAs/month | AI parses/month |
|------|-------|---------|-----------|-----------------|
| **Starter** | TBD (e.g. 1–2) | TBD (e.g. 3–5) | TBD (e.g. 20–25) | TBD (e.g. 25–50) |
| **Professional** | 3 | 10 | 50 | 100 |
| **Enterprise** | 10 | 50 | 200 | 500 |

**Note:** Enterprise can remain **Unlimited** (current behavior) if desired. If so, Professional limits stay as the "highest defined" tier before unlimited. Clarify with product/business before implementation.

### Alternative: Enterprise Stays Unlimited

If Enterprise should remain unlimited:

| Plan | Users | Vessels | DAs/month | AI parses/month |
|------|-------|---------|-----------|-----------------|
| **Starter** | TBD | TBD | TBD | TBD |
| **Professional** | 3 | 10 | 50 | 100 |
| **Enterprise** | Unlimited | Unlimited | Unlimited | Unlimited |

## Scope

### 1. Backend: Update `PLAN_LIMITS` config

- **File:** `backend/app/config.py`
- **Change:** Update `PLAN_LIMITS` dict with new values per table above.
- **Starter values:** Define new Starter limits (lower than current 3/10/50/100) — confirm with product.

### 2. Documentation updates

- **File:** `docs/monetization-plan.md`
- **Change:** Update the plan limits table and `PLAN_LIMITS` code block to match new structure.

### 3. Task/monetization docs

- **File:** `project_epics/08-business-monetization/tasks/task-01-monetization-plan-and-implementation.md`
- **Change:** Update pricing/limits table if it references plan limits.

### 4. Billing / myPOS product mapping

- **Consideration:** If myPOS products are tied to plan IDs (starter, professional, enterprise), ensure product codes and checkout flows still map correctly. No code change if product IDs are unchanged; only limits change.

## Acceptance criteria

- [x] `PLAN_LIMITS` in `backend/app/config.py` reflects new structure (Starter → Professional → Enterprise).
- [x] `docs/monetization-plan.md` is updated with new limits.
- [x] Limits service (`backend/app/services/limits.py`) continues to work — no logic changes needed if it reads from `PLAN_LIMITS`.
- [x] Existing tenants on Starter/Professional/Enterprise retain their plan; only the limits per plan change.
- [x] Billing page and upgrade flows still work (plan names unchanged).

## Related code

- `backend/app/config.py` — `PLAN_LIMITS`
- `backend/app/services/limits.py` — uses `PLAN_LIMITS`
- `backend/app/services/billing.py` — returns limits in subscription status
- `docs/monetization-plan.md` — plan documentation

## References

- [Task 8.1 — Monetization plan](task-01-monetization-plan-and-implementation.md)
- [Task 8.4 — Limits service and feature gating](task-04-limits-service-and-feature-gating.md)
