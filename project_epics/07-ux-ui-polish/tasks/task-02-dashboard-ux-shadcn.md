# Task 7.2 — Dashboard UX with shadcn/ui

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

Redesign the ShipFlow Dashboard with a polished, modern layout using shadcn/ui components, Lucide icons, and maritime-themed design patterns. Transform the current plain layout into a visually engaging, data-rich landing experience.

---

## Problem statement

- **Current state:** Dashboard uses plain divs, basic Tailwind classes, no shadcn components; summary cards are minimal; lists lack visual hierarchy; loading is a generic spinner; empty states are plain text.
- **Pain:** Dashboard feels generic and underutilizes the design system; no charts or trends; weak first impression for users.
- **Goal:** A professional, maritime-themed dashboard with shadcn Cards, icons, skeletons, optional charts, and delightful empty states.

---

## Scope

### 1. Page header & welcome

- **Header:** Use shadcn typography; add a subtle greeting (e.g. "Welcome back" with user name if available).
- **Layout:** Clear hierarchy with `CardTitle`-style page title; optional `CardDescription` for context.
- **Icons:** Lucide `LayoutDashboard` or `Ship` in the header for brand consistency.

### 2. Summary / KPI cards (shadcn Card)

- **Migrate to shadcn Card:** Replace plain divs with `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.
- **Icons per metric:**
  - Total Vessels → `Ship` or `Ships`
  - Total Port Calls → `Anchor` or `MapPin`
  - Active Port Calls → `Activity` or `Radio`
  - Disbursement Accounts → `FileText` or `Receipt`
- **Visual polish:**
  - Icon in a subtle colored circle (e.g. `bg-maritime-100` or `bg-primary/10`) with maritime accent.
  - `CardAction` or footer link styled as shadcn `Button variant="ghost"` or `variant="link"`.
  - Optional: small trend indicator (e.g. `TrendingUp` / `TrendingDown`) if data supports it.
- **Responsive grid:** Keep `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`; ensure cards have consistent height and padding.

### 3. Recent lists (Vessels, Port Calls, DAs)

- **Card layout:** Each list in a shadcn `Card` with `CardHeader` (title + "View all" link), `CardContent`.
- **List items:** Use `Button variant="ghost"` or styled `Link` with hover states; add Lucide icons (e.g. `Ship` for vessels, `Anchor` for port calls, `FileText` for DAs).
- **Badges:** Replace custom `StatusBadge` and `DA_STATUS_COLORS` with shadcn `Badge` and semantic variants (success/error/warning/neutral) + Lucide icons (see Task 7.1).
- **Empty states:** Replace "No vessels yet" with a styled empty state:
  - Centered icon (e.g. `Ship`, `Inbox`, `FileText`) in muted color.
  - Friendly copy: "No vessels yet. Add your first vessel to get started."
  - Optional: `Button` linking to create/add flow.
- **ScrollArea (optional):** If lists can grow long, wrap in shadcn `ScrollArea` with max-height for a cleaner look.

### 4. Loading state (Skeleton)

- **Replace LoadingSpinner:** Use shadcn `Skeleton` for dashboard loading.
- **Skeleton layout:** Mirror the final layout:
  - 4 skeleton cards for summary row.
  - 2 skeleton cards for Recent Vessels / Recent Port Calls.
  - 1 skeleton card for Recent DAs (if permission).
- **Animation:** Skeleton pulse; maintain same grid structure so layout doesn’t jump.

### 5. Error state

- **Replace plain div:** Use shadcn `Alert` with `AlertDescription` for error display.
- **Icon:** `AlertCircle` or `XCircle` from Lucide.
- **Variant:** `destructive` or `variant="destructive"` for errors.

### 6. Optional: Charts (shadcn Chart + Recharts)

- **If scope allows:** Add a simple chart for port call activity (e.g. bar or line chart of port calls over last 7/14 days).
- **Components:** Install shadcn `chart`; use `ChartContainer`, `ChartTooltip`, `ChartTooltipContent`.
- **Data:** Backend may need an endpoint for aggregated port call counts by date; or derive from existing `recentPortCalls` if sufficient.
- **Placement:** New card above or beside Recent lists; maritime-themed colors in chart config.

### 7. Visual polish

- **Spacing:** Consistent `gap-6` between sections; `p-6` in cards.
- **Borders:** Use `border-border` (shadcn token) for consistency.
- **Hover:** Subtle `hover:bg-muted/50` on list items and card links.
- **Maritime theme:** Ensure primary/accent colors align with existing maritime palette (see Task 7.1).

---

## Acceptance criteria

- [ ] Dashboard uses shadcn `Card` for all summary cards and list sections.
- [ ] Each summary card has a Lucide icon (Ship, Anchor, Activity, FileText) in a styled container.
- [ ] Recent Vessels, Port Calls, and DAs use shadcn `Badge` for status (semantic variants + icons).
- [ ] Loading state uses shadcn `Skeleton` matching the dashboard layout (no generic spinner).
- [ ] Error state uses shadcn `Alert` with Lucide icon.
- [ ] Empty states have icons and friendly copy (not plain "No X yet").
- [ ] "View all" links use consistent styling (e.g. `Button variant="ghost"` or `variant="link"`).
- [ ] Maritime theme (primary/maritime colors) applied consistently.
- [ ] Responsive: grid works on mobile (1 col), tablet (2 cols), desktop (4 cols for summary).

---

## Implementation notes

### Summary card example

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Ship, ArrowRight } from "lucide-react";
import { Link } from "react-router";

<Card>
  <CardHeader className="flex flex-row items-center justify-between pb-2">
    <CardTitle className="text-sm font-medium text-muted-foreground">
      Total Vessels
    </CardTitle>
    <div className="rounded-lg bg-maritime-100 p-2">
      <Ship className="size-4 text-maritime-600" />
    </div>
  </CardHeader>
  <CardContent>
    <p className="text-3xl font-bold">{vesselCount}</p>
    <Button variant="link" className="mt-2 h-auto p-0" asChild>
      <Link to="/vessels">
        View all vessels
        <ArrowRight className="ml-1 size-4" />
      </Link>
    </Button>
  </CardContent>
</Card>
```

### Empty state example

```tsx
<div className="flex flex-col items-center justify-center py-12 text-center">
  <div className="rounded-full bg-muted p-4">
    <Ship className="size-8 text-muted-foreground" />
  </div>
  <p className="mt-4 text-sm font-medium text-muted-foreground">
    No vessels yet
  </p>
  <p className="mt-1 text-sm text-muted-foreground">
    Add your first vessel to get started.
  </p>
  <Button variant="outline" className="mt-4" asChild>
    <Link to="/vessels/new">Add vessel</Link>
  </Button>
</div>
```

### Skeleton layout

```tsx
<div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
  {[1, 2, 3, 4].map((i) => (
    <Card key={i}>
      <CardHeader className="space-y-0 pb-2">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-8 w-16" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-9 w-20" />
      </CardContent>
    </Card>
  ))}
</div>
```

### Alert for errors

```tsx
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

<Alert variant="destructive">
  <AlertCircle className="size-4" />
  <AlertDescription>{error}</AlertDescription>
</Alert>
```

### shadcn components to add (if not present)

- `ScrollArea` — for long lists (optional)
- `Separator` — visual separation (optional)
- `Chart` — for optional activity chart

```bash
npx shadcn@latest add scroll-area separator chart
```

---

## Related code

- `frontend/src/pages/Dashboard.tsx` — main target
- `frontend/src/components/ui/card.tsx` — Card, CardHeader, CardTitle, CardContent
- `frontend/src/components/ui/badge.tsx` — status badges
- `frontend/src/components/ui/skeleton.tsx` — loading
- `frontend/src/components/ui/alert.tsx` — errors
- `frontend/src/components/ui/button.tsx` — links and actions

---

## Dependencies

- **Task 7.1** (shadcn, Lucide, Sonner) — should be done first so Card, Badge, Skeleton, Alert, Button are available. If 7.1 is in progress, this task can proceed in parallel for the Dashboard-specific parts.

---

## Out of scope (for now)

- Real-time data (WebSockets).
- Customizable widgets or drag-and-drop layout.
- Dark mode (handled by design system).
- Charts requiring new backend endpoints (include only if data is available from existing API).
