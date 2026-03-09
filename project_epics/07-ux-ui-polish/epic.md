# Epic 7 — UX & UI Polish

**Duration (estimate):** 1–2 weeks

---

## Objective

Elevate the ShipFlow frontend with a modern, consistent design system: shadcn/ui components, Lucide icons, toast notifications (Sonner), and polished interactions across all pages.

---

## Scope

- **shadcn/ui** — Add Button, Card, Input, Dialog, DropdownMenu, and other primitives for consistent, accessible UI.
- **Lucide React** — Replace inline SVGs and add meaningful icons throughout navigation, actions, and status indicators.
- **Sonner** — Replace ad-hoc toast state with a global toast system for success, error, and info feedback.
- **Visual polish** — Consistent spacing, typography, loading states, empty states, and error boundaries.

---

## Tasks

- [Task 7.1](tasks/task-01-shadcn-icons-sonner.md) — shadcn/ui, Lucide icons, Sonner toasts
- [Task 7.2](tasks/task-02-dashboard-ux-shadcn.md) — Dashboard UX with shadcn design
- [Task 7.3](tasks/task-03-platform-rebrand-portnomic.md) — Platform rebrand: ShipFlow → Portnomic (Oxford Blue + Success Green)
- [Task 7.4](tasks/task-04-icon-spacing-sizing.md) — Icon spacing and sizing
- [Task 7.5](tasks/task-05-sidebar-collapse-icon-position.md) — Sidebar collapse: keep icon position, hide text only
- [Task 7.6](tasks/task-06-menu-analysis-redesign.md) — Menu analysis and redesign for better UX
- [Task 7.7](tasks/task-07-topnav-logo-theme.md) — Remove logo from topnav, add light/dark theme switcher
- [Task 7.8](tasks/task-08-dashboard-cards-overlay-bug.md) — Bug: Dashboard cards overlay — vessels/portcalls over disbursements
- [Task 7.9](tasks/task-09-login-page-error-and-input-visibility-bug.md) — Bug: Login page — wrong credentials error not shown, input text not visible

---

## Out of scope (for now)

- Full design system documentation.
- Mobile-specific layouts (responsive basics only).
- Full design system documentation.
- Mobile-specific layouts (responsive basics only).

---

## Acceptance criteria

- [ ] shadcn/ui components available and used across key pages.
- [ ] Lucide icons used consistently for actions, navigation, and status.
- [ ] Sonner toasts replace inline toast state; success/error/info variants work.
- [ ] Pages feel cohesive with improved visual hierarchy and feedback.
