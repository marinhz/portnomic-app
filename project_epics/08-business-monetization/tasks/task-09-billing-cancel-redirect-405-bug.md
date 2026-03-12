# Task 8.9 — Bug: Billing cancel redirect returns 405 Method Not Allowed

**Epic:** [08-business-monetization](../epic.md)

**Type:** Bug

---

## Objective

Fix the bug where users receive **405 Method Not Allowed** when canceling payment at myPOS checkout and being redirected back to the billing page.

## Problem statement

- **User flow:** User clicks "Upgrade to Professional" → redirected to myPOS checkout → user clicks **Cancel** → myPOS redirects to `https://app.portnomic.com/settings/billing?canceled=1`
- **Expected:** User lands on the billing page, sees toast "Checkout was canceled.", params are cleared.
- **Actual:** User sees **405 Method Not Allowed** instead of the billing page.

## Root cause

Per [myPOS Purchase Cancel documentation](https://developers.mypos.com/apis/checkout-api/purchase-cancel):

> myPOS Checkout sends a **POST request** to that URL [URL_Cancel] with a summary of the transaction that was cancelled. The customer is redirected to the URL_Cancel you've provided.

The current `cancel_url` is the **frontend SPA route** (`/settings/billing?canceled=1`). When myPOS redirects the customer, it does so via **POST** (form POST or redirect with POST method). The frontend is served by static hosting (or a server that only accepts GET for SPA routes), which returns **405 Method Not Allowed** for POST requests to non-API paths.

## Scope

### 1. Backend: Add cancel-return endpoint

- **New endpoint:** `POST /api/v1/billing/cancel-return`
- **Purpose:** Accept the POST request from myPOS when the user cancels checkout.
- **Behavior:**
  - Accept POST with `application/x-www-form-urlencoded` body (Amount, Currency, OrderID, Signature per myPOS spec).
  - Optionally verify the Signature using myPOS public certificate (same verification as webhook).
  - Return **302 redirect** to the frontend billing page with `?canceled=1` (e.g. `Location: https://app.portnomic.com/settings/billing?canceled=1`).
- **Auth:** No auth required — myPOS POSTs directly; authenticity is via Signature verification.
- **Config:** Use `CORS_ORIGINS` or `FRONTEND_URL` to determine the redirect target. Ensure the redirect URL is from an allowed origin.

### 2. Frontend: Use backend cancel URL

- **Change:** In `Billing.tsx`, set `cancel_url` to the **backend API endpoint** instead of the frontend route.
- **Example:** `cancel_url = ${apiBaseUrl}/api/v1/billing/cancel-return` (or `${apiBaseUrl}/billing/cancel-return` depending on API prefix).
- **Note:** `success_url` can remain as the frontend URL — verify myPOS success redirect method (GET vs POST). If success also uses POST, apply the same pattern with a `success-return` endpoint.

### 3. Verify success flow

- Check myPOS docs for `URL_OK` (success) redirect method. If it also uses POST, add `POST /api/v1/billing/success-return` and redirect to `?success=1`; otherwise leave success_url as-is.

## Acceptance criteria

- [ ] When user cancels at myPOS checkout, they are redirected to the billing page (no 405).
- [ ] Toast "Checkout was canceled." is shown.
- [ ] URL params are cleared after handling (`setSearchParams({}, { replace: true })`).
- [ ] Cancel-return endpoint verifies myPOS signature (or documents why it is skipped for MVP).
- [ ] Success flow still works (user completing payment lands on billing with `?success=1`).

## Related code

- `frontend/src/pages/settings/Billing.tsx` — `cancel_url`, `success_url`, `?canceled=1` handling
- `backend/app/routers/billing.py` — add `POST /cancel-return`
- `backend/app/services/billing.py` — `verify_mypos_notify` for signature verification (reuse or adapt for cancel params)
- [myPOS Purchase Cancel](https://developers.mypos.com/apis/checkout-api/purchase-cancel)

## References

- [Task 8.7 — Billing page myPOS redesign](task-07-billing-page-mypos-redesign.md) — Success/canceled URL params handling
- [Task 8.6 — Stripe to myPOS migration](task-06-stripe-to-mypos-migration.md) — myPOS integration
