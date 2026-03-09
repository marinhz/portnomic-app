# Task 8.6 — Migrate Billing from Stripe to myPOS

**Epic:** [08-business-monetization](../epic.md)  
**Parent:** [Task 8.3 — Stripe Integration](task-03-stripe-integration.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill. This task requires FastAPI routers, webhook handling, external API integration (myPOS Checkout API), RSA signing, and idempotency — all Backend domain.

---

## Objective

Replace the current Stripe billing integration with myPOS Web Checkout. The app currently uses Stripe for subscription checkout, Customer Portal, and webhooks. myPOS uses a different model: one-time/recurring purchases via hosted checkout, RSA-signed API calls, and server-to-server `URL_Notify` callbacks instead of Stripe-style webhooks.

---

## Documentation

- **Setup & Testing:** [myPOS Initial Setup and Testing](https://developers.mypos.com/online-payments/initial-setup-and-testing)
- **Checkout API:** [myPOS Checkout API Overview](https://developers.mypos.com/apis/checkout-api)
- **Payment Session Create:** [IPCPaymentSessionCreate](https://developers.mypos.com/apis/checkout-api/payment-session-create)
- **Purchase (redirect flow):** [IPCPurchase](https://developers.mypos.com/apis/checkout-api/purchase)
- **Purchase Notify (callback):** [IPCPurchaseNotify](https://developers.mypos.com/apis/checkout-api/purchase-notify)
- **Authentication:** [RSA Signature & Key Pairs](https://developers.mypos.com/apis/checkout-api/checkout-getting-started/authentication)
- **Sandbox:** [Test Data & Credentials](https://developers.mypos.com/online-payments/initial-setup-and-testing/testing-in-sandbox/test-data)
- **Going Live:** [Going Live with myPOS](https://developers.mypos.com/online-payments/initial-setup-and-testing/going-live)

---

## Problem statement

- **Current state:** Billing uses Stripe (Checkout, Customer Portal, webhooks). Tenant model has `stripe_customer_id`, `stripe_subscription_id`; config has Stripe env vars; frontend calls `/billing/create-checkout-session` and `/billing/portal`.
- **Goal:** Switch to myPOS for payment processing. myPOS does not offer a Stripe-style Customer Portal; subscription management will need a different approach (e.g. manual renewal links, or recurring purchases via Mandate/Request Money if applicable).
- **Constraint:** myPOS restricts certain business categories (hosting, streaming, etc.). Maritime agency SaaS may need verification — confirm with myPOS support before full migration.

---

## Scope

### 1. Config and credentials

- **Remove:** `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID_STARTER`, `STRIPE_PRICE_ID_PROFESSIONAL`.
- **Add:** myPOS env vars:
  - `MYPOS_SID` — Store ID
  - `MYPOS_WALLET_NUMBER` — Client number
  - `MYPOS_KEY_INDEX` — Key pair index (e.g. 1)
  - `MYPOS_PRIVATE_KEY` — RSA private key (PEM, for signing requests)
  - `MYPOS_PUBLIC_CERT` — myPOS public certificate (PEM, for verifying notify callbacks)
  - `MYPOS_BASE_URL` — `https://www.mypos.com/vmp/checkout-test` (sandbox) or `https://www.mypos.com/vmp/checkout` (prod)
  - `MYPOS_CURRENCY` — e.g. `EUR`
  - Plan amounts: `MYPOS_AMOUNT_STARTER_MONTHLY`, `MYPOS_AMOUNT_PROFESSIONAL_MONTHLY` (or equivalent)

### 2. Tenant model migration

- Rename or repurpose columns:
  - `stripe_customer_id` → `mypos_customer_id` (optional; myPOS may not require customer IDs for one-time purchases)
  - `stripe_subscription_id` → `mypos_order_id` or `mypos_subscription_ref` (for tracking last/active payment)
- **Migration:** Add Alembic migration to rename columns and backfill if needed. Consider keeping both during transition if doing phased rollout.

### 3. Create checkout flow (replace Stripe Checkout)

- **POST /api/v1/billing/create-checkout-session**
  - Body: `{ "plan": "starter" | "professional", "success_url": "...", "cancel_url": "..." }`
  - **Implementation:**
    1. Build myPOS `IPCPurchase` POST params: `IPCmethod`, `IPCVersion`, `IPCLanguage`, `SID`, `WalletNumber`, `KeyIndex`, `Amount`, `Currency`, `OrderID`, `URL_OK`, `URL_Cancel`, `URL_Notify`, `CartItems`, cart rows, customer email, etc.
    2. `OrderID` = unique per request (e.g. `{tenant_id}-{plan}-{timestamp}`).
    3. Sign: concatenate all values with `-`, base64 encode, RSA-SHA256 sign with private key, add `Signature` to params.
    4. **Option A:** Return `{ "url": "https://www.mypos.com/vmp/checkout-test", "form_data": {...} }` — frontend POSTs form to myPOS (redirect flow).
    5. **Option B:** Backend returns redirect URL that includes a server-side redirect (e.g. backend renders HTML form that auto-submits, or returns 302 with form POST — less common). Simpler: return `form_data` and `url`; frontend builds and submits form.
  - **URL_Notify:** Must be HTTPS, publicly accessible. E.g. `https://api.portnomic.com/api/v1/billing/webhooks/mypos` (or similar). Must return `HTTP 200` with body `OK` or myPOS will reverse the payment.

### 4. Webhook / notify handler (replace Stripe webhooks)

- **POST /api/v1/billing/webhooks/mypos** (no auth; verify via RSA signature)
  - myPOS sends `IPCPurchaseNotify` callback with payment result.
  - **Verification:** Extract `Signature` from POST, remove it from data, concatenate values, base64 encode, verify with myPOS public certificate.
  - **Idempotency:** Use `OrderID` (or equivalent) to avoid duplicate processing. Store in Redis: `shipflow:mypos_events:{OrderID}`.
  - **Logic:** On success, find tenant by `OrderID` (embed `tenant_id` in OrderID or in a custom field if supported), update `plan`, `subscription_status` = `active`, store `mypos_order_id` or similar.
  - **Response:** Return `HTTP 200` with body `OK` (critical — see [Going Live](https://developers.mypos.com/online-payments/initial-setup-and-testing/going-live)).

### 5. Customer Portal replacement

- **Stripe Customer Portal** does not exist in myPOS. Options:
  - **Option A:** Remove "Manage subscription" button; document that users contact support for plan changes/cancellations.
  - **Option B:** Implement a simple "Request cancellation" or "Change plan" flow that creates a new checkout link for the desired plan (downgrade/upgrade as one-time or recurring purchase).
  - **Option C:** Use myPOS [Mandate Management](https://developers.mypos.com/apis/checkout-api/mandate-management) + [Request Money](https://developers.mypos.com/apis/checkout-api/request-money) for recurring pulls — requires separate design.
- **Recommendation:** Start with Option A for MVP; add Option B later if needed.

### 6. Billing service and router

- Refactor `backend/app/services/billing.py`:
  - Remove Stripe SDK usage.
  - Add `mypos_sign_request()`, `mypos_verify_notify()` helpers.
  - `create_checkout_session()` → build IPCPurchase params, sign, return URL + form_data.
  - `process_mypos_notify()` → verify signature, update tenant, idempotency.
- Refactor `backend/app/routers/billing.py`:
  - `POST /create-checkout-session` → call new myPOS flow.
  - `POST /portal` → return 501 with message "Subscription management is not available with myPOS; contact support" (or implement Option B).
  - `POST /webhooks/stripe` → remove or deprecate.
  - `POST /webhooks/mypos` → new notify handler.

### 7. Frontend changes

- `frontend/src/pages/settings/Billing.tsx`:
  - `create-checkout-session` response may change: if backend returns `{ url, form_data }`, frontend must build a form and POST to `url` with `form_data` (or backend could return a redirect URL that does this server-side).
  - "Manage subscription" button: hide or show "Contact support" message when using myPOS.
- No changes to `/billing/status` — it remains plan/usage/limits.

### 8. Dependencies and cleanup

- Remove `stripe` from `pyproject.toml` and `requirements.txt`.
- Add `cryptography` or use stdlib `ssl` for RSA operations if not already present.
- Update `.cursor/rules/business-agent.mdc` — change "Stripe recommended" to "myPOS" if desired.
- Update Epic 8 and task docs to reference myPOS.

---

## Acceptance criteria

### Config & model

- [ ] myPOS env vars documented and configured (sandbox first).
- [ ] Tenant model has `mypos_*` columns (or equivalent); migration applied.
- [ ] Stripe env vars and `stripe` package removed.

### Checkout flow

- [ ] `POST /billing/create-checkout-session` creates myPOS purchase params, signs them, returns URL + form data (or equivalent).
- [ ] Frontend can redirect user to myPOS Checkout page and complete a test payment in sandbox.
- [ ] `URL_Notify` is HTTPS, publicly accessible, and returns `200 OK` with body `OK`.

### Notify handler

- [ ] `POST /billing/webhooks/mypos` verifies RSA signature from myPOS.
- [ ] On successful payment notify, tenant plan and status are updated.
- [ ] Notify processing is idempotent by OrderID.

### Portal

- [ ] "Manage subscription" either disabled with clear message, or replaced with alternative (e.g. "Contact support" or new checkout link for plan change).

### Testing

- [ ] Sandbox tested with [myPOS test credentials](https://developers.mypos.com/online-payments/initial-setup-and-testing/testing-in-sandbox/test-data) and [test cards](https://developers.mypos.com/online-payments/initial-setup-and-testing/testing-in-sandbox/test-cards).
- [ ] Full flow: create checkout → pay in sandbox → notify received → tenant updated.

---

## Implementation notes

### RSA signing (Python)

```python
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

def sign_mypos_request(params: dict, private_key_pem: str) -> str:
    """Concatenate values with '-', base64 encode, RSA-SHA256 sign."""
    values = [str(params[k]) for k in sorted(params.keys()) if k != "Signature"]
    concat = "-".join(values)
    encoded = base64.b64encode(concat.encode()).decode()
    key = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None, backend=default_backend()
    )
    sig = key.sign(encoded.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()
```

### Signature verification (notify)

```python
# Remove Signature from POST data, concatenate, verify with myPOS public cert
# See: https://developers.mypos.com/apis/checkout-api/checkout-getting-started/authentication
```

### Sandbox vs production

| Setting        | Sandbox                          | Production                    |
|----------------|----------------------------------|-------------------------------|
| Base URL       | `https://www.mypos.com/vmp/checkout-test` | `https://www.mypos.com/vmp/checkout` |
| SID            | `000000000000010` (test)         | Your Store ID                 |
| WalletNumber   | `61938166610` (test)             | Your Client number            |
| Private key    | Test key from docs               | Your production key           |
| Public cert    | Test cert from docs              | Remove test cert; use prod    |

---

## Subscription model consideration

myPOS Checkout API is oriented toward **one-time purchases** and **pre-authorization**. For true **recurring subscriptions** (monthly auto-charge), myPOS offers:

- **Mandate Management** + **Request Money** — pull funds from customer's myPOS account on a schedule.
- **Payment Link API** — reusable links for manual renewal.

If the product requires automatic monthly billing (like Stripe subscriptions), evaluate whether myPOS Mandate + Request Money fits, or if monthly "renewal" links are acceptable. This task assumes **manual renewal** or **one-time plan purchase** as the initial approach; recurring automation can be a follow-up task.

---

## Related code

- `backend/app/services/billing.py` — Stripe logic to replace
- `backend/app/routers/billing.py` — routes to refactor
- `backend/app/config.py` — Stripe → myPOS config
- `backend/app/models/tenant.py` — `stripe_*` columns
- `frontend/src/pages/settings/Billing.tsx` — checkout and portal calls
- `project_epics/04-beta-security/tasks/task-14-security-report.md` — URL validation for success/cancel (still apply)

---

## Dependencies

- Task 8.2 (Subscription plan data model) — Tenant, plan, limits
- Task 8.4 (Limits & feature gating) — unchanged
- Task 8.5 (Billing admin UI) — minor updates for "Manage subscription" behavior

---

## Out of scope (for now)

- In-app payment (myPOS In-App Purchase) — redirect flow first.
- Stripe fallback or dual-provider support — clean migration only.
- myPOS Mandate Management for recurring auto-charge — phase 2.
- Legal/compliance review for myPOS terms and restricted categories.
