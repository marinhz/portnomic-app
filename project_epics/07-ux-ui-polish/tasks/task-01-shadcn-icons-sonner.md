# Task 7.1 — shadcn/ui, Lucide icons, Sonner toasts

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

Upgrade the ShipFlow frontend with shadcn/ui components, Lucide React icons, and Sonner toast notifications to deliver a polished, consistent UX across all pages.

---

## Problem statement

- **Current state:** Plain Tailwind buttons, inputs, and tables; inline SVG icons; ad-hoc toast state (e.g. `IntegrationsPage` uses `useState` + a simple div).
- **Pain:** Inconsistent look and feel; no shared component library; manual toast logic in every page; no icon system.
- **Goal:** Professional UI with shadcn/ui, Lucide icons, and a global toast system that any component can trigger.

---

## Scope

### 1. shadcn/ui setup

- **Init:** Run `npx shadcn@latest init` (or equivalent) to add shadcn to the project.
- **Dependencies:** Will add `class-variance-authority`, `clsx`, `tailwind-merge`, `@radix-ui/*` primitives as needed.
- **Components to add:**
  - `Button` — primary, secondary, outline, ghost, destructive variants.
  - `Card` — CardHeader, CardTitle, CardDescription, CardContent, CardFooter.
  - `Input`, `Label` — form fields with consistent styling.
  - `Dialog` — modals for confirmations (e.g. delete email, disconnect integration).
  - `DropdownMenu` — action menus where appropriate.
  - `Badge` — status indicators with semantic variants (success/error/warning/neutral) and icons (see §6).
  - `Tooltip`, `TooltipProvider`, `TooltipTrigger`, `TooltipContent` — for collapsed sidebar nav labels.
  - `Skeleton` — loading placeholders.
  - `Alert`, `AlertDescription` — inline error/info messages.
- **Theme:** Align shadcn theme with existing `maritime` colors (or map `primary` to maritime).

### 2. Lucide React icons

- **Install:** `lucide-react`.
- **Usage:** Replace inline SVGs (e.g. `GmailIcon`, `OutlookIcon`, `ImapIcon`) with Lucide equivalents (`Mail`, `Inbox`, etc.).
- **Apply icons to:**
  - Sidebar navigation (Dashboard, Emails, Port Calls, Vessels, DA, Admin, Settings).
  - Page headers and actions (Sync, Connect, Delete, Edit, Add).
  - Status badges (CheckCircle, XCircle, AlertCircle).
  - Empty states and loading indicators.
  - Form labels and buttons.

### 3. Sonner toast notifications

- **Install:** `sonner`.
- **Setup:** Add `<Toaster />` to the app root (e.g. in `AppLayout` or `main.tsx`).
- **API:** Use `toast.success()`, `toast.error()`, `toast.info()` from any component.
- **Migration:** Replace all ad-hoc toast state (e.g. `IntegrationsPage` `toast` + `setToast`) with Sonner calls.
- **Examples:**
  - `toast.success("Gmail connected successfully!")`
  - `toast.error("Connection failed: access_denied")`
  - `toast.info("Sync complete. No new emails.")`
  - `toast.loading("Syncing…", { id: "sync" })` then `toast.success("Synced 5 new emails", { id: "sync" })` for async flows.

### 4. Component migration (priority pages)

- **IntegrationsPage:** Use Button, Card, Badge, Dialog (for disconnect confirm), Sonner toasts; Lucide icons for Gmail/Outlook/IMAP.
- **EmailList / EmailDetail:** Use DataTable patterns with shadcn, Badge for status, Sonner for delete/parse feedback.
- **PortCallList / VesselList:** Consistent table styling, icons for actions.
- **Admin pages:** Button, Input, Card, Dialog for user/role actions.
- **Sidebar:** Lucide icons for all nav items; collapsible (see §7).

### 5. Loading and empty states

- **LoadingSpinner:** Keep or replace with shadcn `Skeleton` where appropriate.
- **Empty states:** Add icons (e.g. `Inbox` for no emails, `Ship` for no vessels) and friendly copy.

### 6. Status badges (cool variants)

- **Badge variants:** Use shadcn Badge with semantic variants for statuses:
  - **Success** (e.g. `connected`, `completed`, `active`) — green background, `CheckCircle` icon.
  - **Error** (e.g. `error`, `failed`) — red/destructive, `XCircle` icon.
  - **Warning** (e.g. `pending`, `syncing`) — amber/yellow, `AlertCircle` icon.
  - **Neutral** (e.g. `disconnected`, `draft`) — slate/gray, `MinusCircle` or `Circle` icon.
- **Apply to:** Mail connection status (IntegrationsPage), email parse status (EmailList), port call status, DA status.
- **Style:** Rounded pill, icon + label, subtle shadow; ensure good contrast for accessibility.

### 7. Collapsible sidebar

- **Behavior:** Toggle button (e.g. `PanelLeftClose` / `PanelLeft` or `ChevronLeft` / `ChevronRight`) to collapse/expand the left nav.
- **Collapsed state:** Show only icons (no labels); narrow width (e.g. 64px); tooltips on hover for nav items.
- **Expanded state:** Full width with icons + labels (current behavior).
- **Persistence:** Store preference in `localStorage` (e.g. `sidebar-collapsed`) so it survives refresh.
- **Animation:** Smooth width transition (e.g. 200–300ms) when toggling.

---

## Acceptance criteria

- [ ] shadcn/ui initialized; Button, Card, Input, Dialog, Badge, Skeleton, Alert available.
- [ ] Lucide React installed; icons used in Sidebar, IntegrationsPage, and at least 2 other key pages.
- [ ] Sonner Toaster in app root; `toast.success/error/info` used instead of inline toast state.
- [ ] IntegrationsPage fully migrated (buttons, cards, badges, dialog, Sonner).
- [ ] At least one other page (e.g. EmailList or Admin) uses shadcn components and Sonner.
- [ ] Theme aligns with existing maritime branding (primary = maritime).
- [ ] Status badges use semantic variants (success/error/warning/neutral) with icons on IntegrationsPage and at least one other page.
- [ ] Sidebar is collapsible; collapsed state shows icons only with tooltips; preference persisted in localStorage.

---

## Implementation notes

### shadcn init

```bash
npx shadcn@latest init
# Choose: New York style, zinc/slate base, CSS variables for colors
# Then add components: npx shadcn@latest add button card input dialog badge tooltip skeleton alert
```

### Theme alignment

In `globals.css` or shadcn theme, map:

- `--primary` → maritime-600
- `--primary-foreground` → white
- `--destructive` → red-600

### Sonner placement

```tsx
// main.tsx or AppLayout.tsx
import { Toaster } from "sonner";

<>
  <RouterProvider router={router} />
  <Toaster position="top-right" richColors closeButton />
</>
```

### Lucide icon examples

```tsx
import { Mail, Inbox, Settings, Ship, FileText, Users, LayoutDashboard } from "lucide-react";
```

### Status badge variants

```tsx
// Badge with icon for status
<Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100">
  <CheckCircle className="mr-1 size-3.5" />
  connected
</Badge>
<Badge variant="destructive" className="...">
  <XCircle className="mr-1 size-3.5" />
  error
</Badge>
<Badge variant="secondary" className="bg-amber-100 text-amber-800 ...">
  <AlertCircle className="mr-1 size-3.5" />
  syncing
</Badge>
```

### Collapsible sidebar

```tsx
// Sidebar state: isCollapsed from localStorage
const [isCollapsed, setIsCollapsed] = useState(
  () => localStorage.getItem("sidebar-collapsed") === "true"
);
useEffect(() => {
  localStorage.setItem("sidebar-collapsed", String(isCollapsed));
}, [isCollapsed]);

// Collapsed: w-16 (icons only); Expanded: w-56 or w-64
<aside className={cn(
  "flex flex-col border-r transition-all duration-200",
  isCollapsed ? "w-16" : "w-56"
)}>
  <TooltipProvider delayDuration={300}>
    {navItems.map(item => (
      <Tooltip key={item.path}>
        <TooltipTrigger asChild>
          <NavLink to={item.path}>...</NavLink>
        </TooltipTrigger>
        <TooltipContent side="right">{item.label}</TooltipContent>
      </Tooltip>
    ))}
  </TooltipProvider>
  <button onClick={() => setIsCollapsed(!isCollapsed)}>
    {isCollapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
  </button>
</aside>
```

- Add shadcn `Tooltip` for collapsed nav items; `TooltipProvider` wraps the sidebar.

---

## Related code

- `frontend/package.json` — add lucide-react, sonner; shadcn adds its deps
- `frontend/src/main.tsx` — Toaster placement
- `frontend/src/layout/Sidebar.tsx` — nav icons
- `frontend/src/pages/settings/IntegrationsPage.tsx` — primary migration target
- `frontend/src/pages/emails/EmailList.tsx`, `EmailDetail.tsx` — secondary targets
- `frontend/src/components/LoadingSpinner.tsx` — consider Skeleton for tables

---

## Dependencies

- None (standalone UX task; can run in parallel with other epics).

---

## Out of scope (for now)

- Dark mode.
- Animations beyond Sonner’s built-in.
- Full page redesigns (focus on components + icons + toasts).
