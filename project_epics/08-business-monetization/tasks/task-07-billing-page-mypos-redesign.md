# Task 8.7 — Billing Page Redesign for myPOS Compatibility

**Epic:** [08-business-monetization](../epic.md)  
**Parent:** [Task 8.6 — Stripe to myPOS migration](task-06-stripe-to-mypos-migration.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills. This task is primarily React UI changes to the billing page.

---

## Objective

Redesign the Billing settings page so it works correctly with myPOS. The current page assumes Stripe Customer Portal is available; with myPOS, "Manage subscription" is not available. The page must provide a clear, non-confusing experience and offer appropriate alternatives for plan changes and cancellations.

---

## Problem statement

- **Current state:** The billing page at `/settings/billing` shows a "Manage subscription" button that calls `POST /billing/portal`. With myPOS, the backend returns `501 NOT IMPLEMENTED` with `PORTAL_UNAVAILABLE` — myPOS has no Customer Portal.
- **User experience:** Clicking "Manage subscription" always shows a toast: "Subscription management is not available. Contact support for plan changes or cancellations." This is confusing and makes the button feel broken.
- **Goal:** Redesign the page so it is myPOS-compatible: remove or replace the portal button, provide clear alternatives (contact support, change plan via checkout), and update copy to reflect the current billing provider.

---

## Scope

### 1. Replace "Manage subscription" with myPOS-appropriate actions

- **Remove** the "Manage subscription" button that calls `/billing/portal` (or hide it when portal is unavailable).
- **Add** one or more of:
  - **"Contact support"** — Link or button that opens email to support (e.g. `mailto:support@portnomic.com?subject=Plan change or cancellation`) or displays support contact info.
  - **"Change plan"** — For upgrades: use existing "Upgrade to Professional" flow. For downgrades: either a "Request downgrade" that contacts support, or a new checkout session for the target plan (if backend supports it).
  - **"Request cancellation"** — Link or button that directs user to contact support for cancellations.

### 2. Update page copy and messaging

- **Page description:** Change from "View your plan, usage, and manage your subscription" to wording that does not imply self-service portal (e.g. "View your plan, usage, and contact support for plan changes or cancellations").
- **Card description:** Update "Current subscription plan and status" if needed.
- **Info callout (optional):** Add a subtle info message: "Plan changes and cancellations are handled by our support team. Contact us for assistance."

### 3. Optional: Backend support for provider detection

- If desired, add `GET /billing/status` response field: `portal_available: boolean` (or `billing_provider: "mypos" | "stripe"`). Frontend can conditionally show "Manage subscription" only when `portal_available === true`.
- **Simpler approach:** Assume myPOS (portal unavailable) for now; remove portal button entirely. Re-add when/if Stripe or another provider with portal is supported.

### 4. Preserve existing functionality

- **Upgrade flow:** Keep "Upgrade to Professional" (or equivalent) — it uses `create-checkout-session` and works with myPOS.
- **Usage table:** No changes — plan, status, usage, limits remain as-is.
- **Success/canceled URL params:** Keep handling `?success=1` and `?canceled=1` for checkout return.

---

## Acceptance criteria

- [ ] "Manage subscription" button is removed or replaced with myPOS-appropriate alternative(s).
- [ ] Users can clearly see how to contact support for plan changes or cancellations (mailto link, support email, or equivalent).
- [ ] Page copy does not imply that a self-service portal exists.
- [ ] "Upgrade to Professional" (or equivalent) still works and redirects to myPOS checkout.
- [ ] Usage table and plan/status display remain functional.
- [ ] No confusing toast when user expects portal — button either does something useful or is not shown.

---

## Implementation notes

### Suggested UI changes

1. **Replace "Manage subscription" with "Contact support" button:**
   - `mailto:support@portnomic.com?subject=ShipFlow%20-%20Plan%20change%20or%20cancellation`
   - Or use a configurable support email from env/config.

2. **Optional "Change plan" for downgrades:**
   - If user is on Professional and wants Starter: show "Request downgrade" → contact support.
   - Or: backend could add `POST /billing/create-checkout-session` support for `plan: "starter"` when downgrading (one-time purchase for new plan) — out of scope for this task unless specified.

3. **Info alert:**
   ```tsx
   <Alert>
     <AlertDescription>
       Plan changes and cancellations are handled by our support team.{" "}
       <a href="mailto:support@portnomic.com" className="underline">
         Contact support
       </a>{" "}
       for assistance.
     </AlertDescription>
   </Alert>
   ```

---

## Related code

- `frontend/src/pages/settings/Billing.tsx` — main page to redesign
- `backend/app/routers/billing.py` — `POST /portal` returns 501 for myPOS
- [Task 8.6](task-06-stripe-to-mypos-migration.md) — myPOS migration (portal replacement)

---

## Dependencies

- Task 8.6 (Stripe → myPOS migration) — billing backend uses myPOS; portal returns 501
- Task 8.5 (Billing admin UI) — existing billing page structure

---

## Out of scope

- Backend changes to support Stripe portal in future (dual-provider) — focus on myPOS-only for now
- myPOS Mandate Management or recurring auto-charge — separate task
- Plan comparison table or pricing page
