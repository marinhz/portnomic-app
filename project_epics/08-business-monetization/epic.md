# Epic 8 — Business & Monetization

**Source:** Business strategy, post–core-infrastructure  
**Duration (estimate):** 3–4 weeks

---

## Agent assignments

| Task | Agent | Skills |
|------|-------|--------|
| 8.1 Monetization plan | Backend | fastapi-python, python-project-structure |
| 8.2 Subscription data model | Backend | fastapi-python, python-project-structure |
| 8.3 Stripe integration | Backend | fastapi-python |
| 8.4 Limits & feature gating | Backend | fastapi-python, python-project-structure |
| 8.5 Billing admin UI | Frontend | react-dev, react-router-v7, tailwind-design-system |
| 8.6 Stripe → myPOS migration | Backend | fastapi-python |
| 8.7 Billing page myPOS redesign | Frontend | react-dev, react-router-v7, tailwind-design-system |

---

## Objective

Define and implement a monetization model for ShipFlow AI so that maritime agencies can subscribe, pay, and receive value-aligned access to features. Deliver subscription management, billing integration, and feature gating tied to plan tiers.

---

## Scope

### Business model

- **Tiered SaaS subscription** — Starter, Professional, Enterprise (or equivalent).
- **Usage-based add-ons** — Optional overage for DAs, vessels, or AI parse volume.
- **Annual vs monthly** — Support both; annual discount for enterprise.

### Technical scope

- **Billing provider** — Stripe (current); Task 8.6 migrates to myPOS.
- **Tenant subscription state** — Plan, status (active/trial/canceled), limits.
- **Feature gating** — Enforce limits (users, vessels, DAs/month) and feature access by plan.
- **Admin UI** — Billing overview, plan change, usage display (optional).

---

## Out of scope (for now)

- In-app payment collection (Stripe Checkout handles).
- Complex usage metering (e.g. per-API-call); focus on high-level limits.
- Legal/commercial terms and SLAs (separate legal process).

---

## Acceptance criteria

- [ ] Monetization strategy documented (pricing tiers, limits, add-ons).
- [ ] Tenant has subscription plan and status; limits enforced in backend.
- [ ] Stripe integration: create customer, subscription, handle webhooks.
- [ ] Feature gating: AI parse, DA generation, user count respect plan limits.
- [ ] Admin can view subscription status and upgrade/downgrade (or via Stripe portal).

---

## EDD references

- §3 Architecture overview (multi-tenancy)
- §5 Data model (tenant, user)
- Task 1.20 (multitenant companies) — billing explicitly deferred; this epic addresses it
