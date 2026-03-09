# Task 8.3 — Stripe Integration (Checkout, Portal, Webhooks)

**Epic:** [08-business-monetization](../epic.md)  
**Parent:** [Task 8.1 — Monetization plan](task-01-monetization-plan-and-implementation.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill. This task requires FastAPI routers, webhook handling, external API integration (Stripe SDK), and idempotency — all Backend domain.

---

## Objective

Integrate Stripe for subscription billing: create checkout sessions for new subscriptions, provide Customer Portal for self-service management, and handle webhooks to keep tenant subscription state in sync.

---

## Scope

### 1. Stripe SDK and config

- Add `stripe` Python package to dependencies.
- Env vars: `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_STARTER`, `STRIPE_PRICE_ID_PROFESSIONAL` (or single product with multiple prices).
- Add to `config.py` / settings.

### 2. Create Checkout session

- **POST /api/v1/billing/create-checkout-session**
  - Body: `{ "plan": "starter" | "professional", "success_url": "...", "cancel_url": "..." }`
  - Creates or retrieves Stripe customer for tenant; creates Checkout session for subscription.
  - Returns `{ "url": "https://checkout.stripe.com/..." }` — frontend redirects user.
  - Requires authenticated tenant user (admin or billing role).

### 3. Customer Portal

- **POST /api/v1/billing/portal**
  - Body: `{ "return_url": "..." }`
  - Creates Stripe Customer Portal session for tenant's Stripe customer.
  - Returns `{ "url": "https://billing.stripe.com/..." }` — frontend opens in new tab.
  - Allows tenant to manage subscription, payment method, view invoices.

### 4. Webhook handler

- **POST /api/v1/billing/webhooks/stripe** (or `/webhooks/stripe` — no auth; verify via signature)
  - Verify `stripe-signature` header with `STRIPE_WEBHOOK_SECRET`.
  - Handle events:
    - `customer.subscription.created` — link subscription to tenant, set plan and status.
    - `customer.subscription.updated` — update plan, status (active/canceled/past_due).
    - `customer.subscription.deleted` — set status to `canceled`, clear `stripe_subscription_id`.
    - `invoice.paid` — optional: record payment for audit.
    - `invoice.payment_failed` — optional: set `past_due`, notify.
  - **Idempotency:** Store processed `event.id`; skip if already processed.
  - Use `BackgroundTasks` for non-blocking processing if needed.

### 5. Billing router and service

- `backend/app/routers/billing.py` — routes for checkout, portal, webhook.
- `backend/app/services/billing.py` — Stripe API calls, tenant updates.
- Webhook route must NOT use tenant middleware (Stripe calls with no JWT).

---

## Acceptance criteria

- [x] Stripe SDK installed; env vars configured.
- [x] `POST /api/v1/billing/create-checkout-session` creates session and returns redirect URL.
- [x] `POST /api/v1/billing/portal` creates portal session and returns URL.
- [x] Webhook handler processes `customer.subscription.*` and `invoice.*`; updates tenant state.
- [x] Webhook processing is idempotent (by Stripe event ID).
- [ ] Stripe products/prices configured in Stripe Dashboard (manual setup).

---

## Implementation notes

### Webhook verification

```python
payload = await request.body()
sig = request.headers.get("stripe-signature")
event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
```

### Idempotency

- Store `stripe_event_id` in a table (e.g. `processed_stripe_events`) or Redis.
- Before processing: `if await already_processed(event.id): return 200`

---

## Related code

- `backend/app/routers/billing.py` — new router
- `backend/app/services/billing.py` — new service
- `backend/app/config.py` — Stripe env vars

---

## Dependencies

- Task 8.2 (Subscription plan data model) — Tenant has Stripe ID columns
