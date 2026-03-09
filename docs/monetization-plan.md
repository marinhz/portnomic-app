# ShipFlow AI — Monetization Plan

**Epic:** [08 — Business & Monetization](../project_epics/08-business-monetization/epic.md)

---

## 1. Pricing Model

| Tier | Target | Users | Vessels | DAs/month | AI parse | Price (example) |
|------|--------|-------|---------|-----------|----------|------------------|
| **Starter** | Small agencies | 3 | 10 | 50 | 100 | €99/mo |
| **Professional** | Mid-size | 10 | 50 | 200 | 500 | €299/mo |
| **Enterprise** | Large / custom | Unlimited | Unlimited | Unlimited | Unlimited | Custom |

### Add-ons and Discounts

- **Usage overage:** Optional add-on for DAs or AI parses beyond plan (e.g. €0.50/DA over cap).
- **Annual discount:** 15–20% for annual prepay.
- **Trial:** 14-day free trial for new tenants (optional).

---

## 2. Feature Gating by Plan

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

---

## 3. Limits Enforcement

| Limit | Behavior |
|-------|----------|
| **Users** | Block user creation when at plan limit; show upgrade CTA. |
| **Vessels** | Block vessel creation when at limit. |
| **DAs/month** | Reset counter monthly; block DA generation when over limit; optionally allow overage (billable). |
| **AI parse** | Count parsed emails; block or throttle when over limit. |

---

## 4. Plan Limits (Technical Reference)

```python
PLAN_LIMITS = {
    "starter": {
        "users": 3,
        "vessels": 10,
        "das_per_month": 50,
        "ai_parses_per_month": 100,
    },
    "professional": {
        "users": 10,
        "vessels": 50,
        "das_per_month": 200,
        "ai_parses_per_month": 500,
    },
    "enterprise": {
        "users": None,
        "vessels": None,
        "das_per_month": None,
        "ai_parses_per_month": None,
    },  # unlimited
}
```

---

## 5. Implementation Roadmap

| Task | Description |
|------|-------------|
| [8.2 — Subscription plan data model](../project_epics/08-business-monetization/tasks/task-02-subscription-plan-data-model.md) | Add plan, subscription_status, Stripe IDs to Tenant; migration |
| [8.3 — Stripe integration](../project_epics/08-business-monetization/tasks/task-03-stripe-integration.md) | Checkout session, Customer Portal, webhook handler |
| [8.4 — Limits service and feature gating](../project_epics/08-business-monetization/tasks/task-04-limits-service-and-feature-gating.md) | Enforce user, vessel, DA, AI parse limits; 403 upgrade_required |
| [8.5 — Billing admin UI](../project_epics/08-business-monetization/tasks/task-05-billing-admin-ui.md) | (Optional) Billing page with plan, usage, upgrade/manage buttons |

---

## 6. Out of Scope

- In-app payment form (Stripe Checkout/Portal handles).
- Complex usage metering (per-API-call); focus on high-level limits.
- Legal terms, SLAs, contracts.
