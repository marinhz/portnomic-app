# Task 8.1 — Monetization Plan and Implementation

**Epic:** [08-business-monetization](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills. This task defines the technical foundation; the Backend agent owns API design, config, and integration patterns. Consider the **Business Agent** rule (`.cursor/rules/business-agent.mdc`) for monetization principles and tier alignment.

---

## Objective

Define a monetization strategy for ShipFlow AI and implement the technical foundation: subscription plans, billing integration (Stripe), tenant limits, and feature gating so that the product can generate recurring revenue from maritime agency tenants.

---

## Problem statement

- **Current state:** ShipFlow is multi-tenant but has no billing or subscription logic. Task 1.20 explicitly deferred "billing or subscription per tenant."
- **Pain:** No revenue model; no way to charge for value delivered (DA automation, AI parsing, workload reduction).
- **Goal:** A clear monetization plan plus working subscription and feature-gating implementation.

---

## Monetization Plan

### 1. Pricing model (recommended)

| Tier | Target | Users | Vessels | DAs/month | AI parse | Price (example) |
|------|--------|-------|---------|-----------|----------|------------------|
| **Starter** | Small agencies | 2 | 5 | 25 | 50 | €99/mo |
| **Professional** | Mid-size | 3 | 10 | 50 | 100 | €299/mo |
| **Enterprise** | Large / custom | Unlimited | Unlimited | Unlimited | Unlimited | Custom |

- **Usage overage:** Optional add-on for DAs or AI parses beyond plan (e.g. €0.50/DA over cap).
- **Annual discount:** 15–20% for annual prepay.
- **Trial:** 14-day free trial for new tenants (optional).

### 2. Feature gating by plan

| Feature | Starter | Professional | Enterprise |
|---------|---------|--------------|------------|
| Vessel & port call CRUD | ✓ | ✓ | ✓ |
| AI email parsing | ✓ (capped) | ✓ (capped) | ✓ |
| DA generation & approval | ✓ (capped) | ✓ (capped) | ✓ |
| Email dispatch | ✓ | ✓ | ✓ |
| OAuth Gmail/Outlook | ✓ | ✓ | ✓ |
| Audit logs | Basic | Full | Full |
| API access | — | ✓ | ✓ |
| Dedicated support | — | — | ✓ |

### 3. Limits enforcement

- **Users:** Block user creation when at plan limit; show upgrade CTA.
- **Vessels:** Block vessel creation when at limit.
- **DAs/month:** Reset counter monthly; block DA generation when over limit; optionally allow overage (billable).
- **AI parse:** Count parsed emails; block or throttle when over limit.

---

## Scope

Implementation is split into sub-tasks:

| Task | Description |
|------|-------------|
| [8.2 — Subscription plan data model](task-02-subscription-plan-data-model.md) | Add plan, subscription_status, Stripe IDs to Tenant; plan limits config; migration |
| [8.3 — Stripe integration](task-03-stripe-integration.md) | Checkout session, Customer Portal, webhook handler |
| [8.4 — Limits service and feature gating](task-04-limits-service-and-feature-gating.md) | Enforce user, vessel, DA, AI parse limits; 403 upgrade_required |
| [8.5 — Billing admin UI](task-05-billing-admin-ui.md) | (Optional) Billing page with plan, usage, upgrade/manage buttons |

---

## Acceptance criteria

*Satisfied by sub-tasks 8.2–8.5.*

- [ ] Monetization plan documented (tiers, limits, pricing examples) in this task or `docs/monetization-plan.md`.
- [ ] Tenant has `plan`, `subscription_status`, Stripe IDs; migration applied.
- [ ] Stripe Checkout creates subscription; webhook updates tenant state.
- [ ] Stripe Customer Portal allows tenant to manage subscription and payment method.
- [ ] User creation blocked when at plan user limit; returns 403 with upgrade message.
- [ ] Vessel creation blocked when at plan vessel limit.
- [ ] DA generation blocked when over monthly DA limit (or overage flow if implemented).
- [ ] AI parse blocked or throttled when over monthly parse limit.
- [ ] (Optional) Admin UI shows plan, usage, and link to Stripe portal.

---

## Implementation notes

### Backend — plan limits config

```python
# config or constants (restructured Task 8.10)
PLAN_LIMITS = {
    "starter": {"users": 2, "vessels": 5, "das_per_month": 25, "ai_parses_per_month": 50},
    "professional": {"users": 3, "vessels": 10, "das_per_month": 50, "ai_parses_per_month": 100},
    "enterprise": {"users": None, "vessels": None, "das_per_month": None, "ai_parses_per_month": None},  # unlimited
}
```

### Backend — limit check

```python
# services/limits.py
async def check_user_limit(db, tenant_id: UUID) -> bool:
    plan = await get_tenant_plan(db, tenant_id)
    limit = PLAN_LIMITS[plan].get("users")
    if limit is None:
        return True
    count = await count_users(db, tenant_id)
    return count < limit
```

### Stripe webhook

```python
# routers/billing.py
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    # Handle subscription.*, invoice.* — update tenant
    # Use event.id for idempotency
```

---

## Related code

- `backend/app/models/tenant.py` (or company) — add subscription fields
- `backend/app/services/limits.py` — new service
- `backend/app/routers/billing.py` — new router
- `backend/app/config.py` — Stripe env vars
- `frontend/src/pages/settings/Billing.tsx` — optional UI

---

## Dependencies

- Task 1.20 (Multitenant companies) — tenant/company model exists
- Stripe account and products/prices configured in Stripe Dashboard

---

## Out of scope

- In-app payment form (Stripe Checkout/Portal handles).
- Complex usage metering (per-API-call); focus on high-level limits.
- Legal terms, SLAs, contracts.
