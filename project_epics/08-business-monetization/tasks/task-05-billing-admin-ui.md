# Task 8.5 — Billing Admin UI (Optional)

**Epic:** [08-business-monetization](../epic.md)  
**Parent:** [Task 8.1 — Monetization plan](task-01-monetization-plan-and-implementation.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills. This task is primarily React UI (settings page, usage display, Stripe redirects). If `GET /billing/status` is added, coordinate with **Backend** agent for that endpoint.

---

## Objective

Add a Billing section in Settings or Admin where tenant admins can view their current plan, usage (users, vessels, DAs this month), and manage their subscription via Stripe Customer Portal.

---

## Scope

### 1. Billing API (if not exists)

- **GET /api/v1/billing/status** — returns:
  - `plan`, `subscription_status`
  - `usage`: `{ "users": N, "vessels": N, "das_this_month": N, "ai_parses_this_month": N }`
  - `limits`: from `PLAN_LIMITS[plan]`
- Requires authenticated tenant user.

### 2. Billing page (frontend)

- **Route:** `/settings/billing` or `/admin/billing` (behind tenant admin).
- **Content:**
  - Current plan name and status badge (Active, Trial, Past Due, Canceled).
  - Usage table: users (X / limit), vessels (X / limit), DAs this month (X / limit), AI parses (X / limit).
  - "Upgrade" button — calls `POST /api/v1/billing/create-checkout-session`, redirects to Stripe Checkout.
  - "Manage subscription" button — calls `POST /api/v1/billing/portal`, opens Stripe Customer Portal in new tab.

### 3. Upgrade CTA

- When user hits a limit (403 upgrade_required), frontend can show a toast or modal with link to `/settings/billing` or direct Stripe Checkout.

---

## Acceptance criteria

- [ ] Billing page shows current plan, status, and usage.
- [ ] "Manage subscription" opens Stripe Customer Portal in new tab.
- [ ] "Upgrade" creates checkout session and redirects to Stripe Checkout.
- [ ] Usage numbers match backend limits (users, vessels, DAs, AI parses).

---

## Related code

- `frontend/src/pages/settings/Billing.tsx` — new page
- `backend/app/routers/billing.py` — add `GET /billing/status` if needed

---

## Dependencies

- Task 8.3 (Stripe integration) — checkout and portal endpoints exist
- Task 8.4 (Limits service) — usage counts available

---

## Out of scope

- In-app payment form (Stripe handles).
- Plan comparison table (can be static content).
