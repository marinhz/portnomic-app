# Task 8.8 — Plan Upgrade Gate Page (Cool Upgrade Experience)

**Epic:** [08-business-monetization](../epic.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

When a user on a lower plan (e.g. Starter) clicks a feature that requires a higher plan (e.g. AI Settings), they land on a **cool, polished upgrade gate page** instead of a generic error. The page shows the full context (e.g. AI Settings layout) with a clear, prominent message: "AI settings are available on Professional and Enterprise plans." and a CTA to upgrade.

---

## Scenario (User Story)

- **As a** user on the Starter plan  
- **I** see the AI Settings icon in the left sidebar  
- **When I** click it  
- **I** land on the AI Settings page and see the full layout with a clear upgrade message: "AI settings are available on Professional and Enterprise plans."  
- **So that** I understand what I'm missing and can easily upgrade

---

## Problem statement

- **Current state:** When a Starter-plan user accesses AI Settings (`/settings/ai`), the API returns 403 with `upgrade_required`. The page may show a small banner or error. The experience feels like a dead end.
- **Pain:** Users don't get a compelling reason to upgrade; the upgrade prompt is easy to miss or feels like a generic error.
- **Goal:** A dedicated "upgrade gate" experience: show the page structure (header, tabs, layout) with a prominent, visually appealing upgrade card/message and CTA to Billing/plans.

---

## Scope

### 1. Sidebar: Show AI Settings for all users with settings access

- **Location:** `frontend/src/layout/Sidebar.tsx`
- **Change:** AI Settings nav item is shown to users with `settings:write` or `is_platform_admin` (current behavior). No change needed if plan check happens only on the page/API.
- **If AI Settings is currently hidden for Starter users:** Ensure the sidebar shows the AI icon for all users who have permission to see Settings, regardless of plan. Plan gating happens on the page, not in the sidebar.

### 2. Upgrade gate page design

- **Location:** `frontend/src/pages/settings/AISettingsPage.tsx` (or a shared `PlanUpgradeGate` component for reuse)
- When `upgrade_required` (403 from API) or when plan is known to be Starter on load:
  - Show the **full page layout** (header "AI Settings", tabs for Integration / Prompts if applicable)
  - Replace the main content area with a **cool upgrade gate card**:
    - Icon (e.g. Sparkles, Lock, or Zap)
    - Headline: "AI settings are available on Professional and Enterprise plans."
    - Short description: What they get (e.g. "Configure your own AI provider, customize prompts, and more.")
    - Primary CTA: "Upgrade plan" → links to `/settings/billing`
    - Optional: "View plans" or "Compare plans" link
  - Design: Use Card, Alert, or a custom hero-style block. Match design system (Epic 7). Consider a subtle gradient or illustration for a "premium" feel.

### 3. Reusable pattern (optional)

- If other features will be plan-gated (e.g. Emissions, advanced reports), consider a shared `PlanUpgradeGate` component:
  - Props: `featureName`, `requiredPlans`, `description`, `icon`
  - Renders the upgrade card consistently across pages.

### 4. Backend alignment

- Backend already returns 403 with `{"code": "upgrade_required", "message": "AI settings are available on Professional and Enterprise plans.", "limit_type": "ai_settings"}` (Task 10.4).
- Frontend should use `message` from the API when available; fallback to default copy.

---

## Acceptance criteria

### AI Settings upgrade gate

- [ ] Starter-plan user with `settings:write` sees AI Settings in sidebar and can click it.
- [ ] On `/settings/ai`, when API returns 403 `upgrade_required`, user sees the full page layout (header, structure) with a prominent upgrade card.
- [ ] Upgrade card displays: "AI settings are available on Professional and Enterprise plans." (or API message).
- [ ] CTA button "Upgrade plan" links to `/settings/billing`.
- [ ] Page is visually polished (not a bare error state).

### UX

- [ ] No jarring redirect or 404; user stays on the page and understands the situation.
- [ ] Dark mode: upgrade card looks good in both themes.
- [ ] Mobile: layout remains usable.

### Edge cases

- [ ] If user loses plan mid-session (e.g. downgrade), next API call returns 403; page shows upgrade gate.
- [ ] Admin users on premium plans see the normal AI Settings form (no regression).

---

## Implementation notes

### Example upgrade gate layout

```tsx
// When upgradeRequired === true:
<div className="flex flex-col items-center justify-center py-16 px-4">
  <div className="max-w-md w-full">
    <Card className="border-2 border-mint-200 dark:border-mint-800 bg-mint-50/50 dark:bg-mint-950/30">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-mint-100 dark:bg-mint-900 p-3">
            <Sparkles className="size-8 text-mint-600 dark:text-mint-400" />
          </div>
          <div>
            <CardTitle>AI settings are available on Professional and Enterprise plans.</CardTitle>
            <CardDescription>
              Configure your own AI provider, customize parsing prompts, and more.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Button asChild>
          <Link to="/settings/billing">Upgrade plan</Link>
        </Button>
      </CardContent>
    </Card>
  </div>
</div>
```

### Plan detection

- Use existing 403 `upgrade_required` response from API (no new endpoint needed).
- Optional: If `GET /billing/status` or similar exposes `plan`, frontend could show upgrade gate without waiting for API failure (faster UX).

---

## Related code

- `frontend/src/pages/settings/AISettingsPage.tsx` — upgrade gate UI
- `frontend/src/layout/Sidebar.tsx` — AI Settings nav visibility
- `frontend/src/auth/AdminAISettingsRoute.tsx` — route protection (permission, not plan)
- `backend/app/routers/settings.py` or `ai_settings.py` — 403 upgrade_required response

---

## Dependencies

- Task 10.4 — API returns 403 `upgrade_required` for non-premium tenants
- Task 10.5 — AI Settings page structure
- Task 8.7 — Billing page for upgrade CTA destination

---

## Out of scope (for now)

- Hiding AI Settings from sidebar for Starter users (user explicitly wants to see it and get the upgrade message)
- Plan upgrade gate for other features (Emissions, etc.) — can be added later using same pattern
