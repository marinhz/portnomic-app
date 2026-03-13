# Task 8.11 — Change All Upgrade Plan Buttons to Contact Support (Until myPOS Key Available)

**Epic:** [08-business-monetization](../epic.md)

---

## Scenario

Until a myPOS API key is configured and the checkout flow is live, all upgrade plan buttons should direct users to contact support instead of attempting myPOS checkout. This avoids broken or confusing UX when users click "Upgrade to Professional" and the backend cannot process the request.

---

## Objective

Replace all upgrade/checkout buttons across the app with "Contact support" (mailto) links until myPOS credentials are available. Users can still express interest and reach support; they are not blocked from upgrading, but the flow is manual until the integration is ready.

---

## Scope

### 1. Billing page (`frontend/src/pages/settings/Billing.tsx`)

**Purchase options section:**

- **Starter / Professional:** Currently buttons that call `handlePurchase` → `POST /billing/create-checkout-session` and redirect to myPOS.
- **Change:** Replace all "Upgrade to Professional", "Upgrade to Starter", "Purchase Starter" buttons with **"Contact support"** mailto links.
- Use the same pattern as Enterprise: `mailto:support@portnomic.com?subject=ShipFlow%20-%20{PlanName}%20plan`.
- Keep the same visual layout (plan cards, descriptions).

**Optional:** Keep `handlePurchase` and `create-checkout-session` logic but hidden behind a feature flag or env check so it can be re-enabled later without code changes. For now, simpler: just remove the checkout flow and use mailto for all.

### 2. PlanUpgradeGate component (`frontend/src/components/PlanUpgradeGate.tsx`)

- **Current:** "Upgrade plan" and "View plans" buttons link to `/settings/billing`.
- **Change:** Replace with **"Contact support"** mailto link (primary CTA) and optionally keep "View plans" as secondary (or link to billing page for plan info only, since billing page will also show contact support).
- **Recommendation:** Primary CTA = "Contact support" (mailto). Secondary = "View plans" (link to billing) — still useful for plan comparison.

---

## Acceptance criteria

- [ ] Billing page: All Starter and Professional plan buttons show "Contact support" (mailto) instead of checkout redirect.
- [ ] PlanUpgradeGate: Primary CTA is "Contact support" (mailto); secondary can remain "View plans" → billing.
- [ ] No calls to `POST /billing/create-checkout-session` from the frontend for plan purchase.
- [ ] Copy is clear: users understand they should contact support to upgrade.
- [ ] Easy to revert: when myPOS key is available, buttons can be switched back (document or structure code so this is straightforward).

---

## Implementation notes

### Billing.tsx

- For plans where `canPurchaseViaCheckout` was true, use the same "Contact support" pattern as Enterprise:
  ```tsx
  <Button variant="outline" asChild size="sm">
    <a href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(`ShipFlow - ${plan.name} plan`)}`}>
      Contact support
    </a>
  </Button>
  ```
- Remove or comment out `handlePurchase`, `purchasingPlan` state, and checkout logic if no longer needed.
- Update "Purchase options" card description: e.g. "Contact support to upgrade or change your plan."

### PlanUpgradeGate.tsx

- Add optional prop: `contactSupportEmail?: string` (default: `support@portnomic.com`).
- When `contactSupportEmail` is set (or a new prop `useContactSupport?: boolean`), render mailto instead of Link to billing.
- Or simpler: always use mailto for primary CTA until myPOS is ready; can add a prop later to toggle.

---

## Related code

- `frontend/src/pages/settings/Billing.tsx` — purchase buttons
- `frontend/src/components/PlanUpgradeGate.tsx` — upgrade gate CTAs
- `frontend/src/pages/settings/AISettingsPage.tsx` — uses PlanUpgradeGate

---

## Dependencies

- Task 8.6 (Stripe → myPOS migration) — myPOS integration; this task is a temporary workaround until myPOS key is available.
- Task 8.7 (Billing page myPOS redesign) — billing page structure.

---

## Revert plan

When myPOS key is configured:

1. Restore `handlePurchase` and checkout flow in Billing.tsx for Starter/Professional.
2. Restore PlanUpgradeGate primary CTA to "Upgrade plan" → billing page.
3. Consider adding `MYPOS_ENABLED` or similar env flag to toggle between contact-support and checkout modes for future flexibility.

---

## Priority

Medium — Unblocks clean UX until myPOS is ready; avoids users hitting broken checkout.
