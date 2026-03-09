# Task 7.6 — Menu analysis and redesign for better UX

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

Analyze the current sidebar navigation menu, identify UX pain points and improvement opportunities, and design a new menu structure that improves discoverability, task flow, and overall user experience for Portnomic (maritime agency SaaS).

---

## Problem statement

- **Current state:** The sidebar menu has grown organically with sections (Financial, AI Processing, Settings, Admin), permission-based visibility, and a flat list of nav items. No formal UX analysis has been done.
- **Pain:** Users may struggle to find features, understand the information architecture, or complete common workflows efficiently. Section labels and grouping may not match mental models.
- **Goal:** A menu that is intuitive, scannable, and aligned with how maritime agency users think and work.

---

## Scope

### Phase 1 — Analysis (audit)

1. **Current menu inventory**
   - Document all nav items, sections, and permission gates.
   - Map routes and nested pages (e.g. vessels/:id, da/:id).
   - Note which items are primary vs secondary vs admin-only.

2. **User journey mapping**
   - Identify common workflows (e.g. vessel → port call → DA → email).
   - Map how users move between sections today.
   - Identify friction points (e.g. too many clicks, unclear labels).

3. **Competitive / pattern research**
   - Review navigation patterns in similar B2B SaaS (maritime, logistics, agency tools).
   - Consider: grouped nav, mega-menus, quick actions, search, breadcrumbs.

4. **Accessibility & usability**
   - Keyboard navigation, screen reader support, focus management.
   - Touch targets, contrast, and clarity of active state.

### Phase 2 — Redesign

1. **Information architecture**
   - Propose a new structure (sections, groupings, hierarchy).
   - Consider: task-based vs entity-based organization.
   - Decide: flat list vs nested/collapsible groups.

2. **Visual design**
   - Section dividers, spacing, typography hierarchy.
   - Active state, hover, and focus indicators.
   - Collapsed vs expanded behavior (align with Task 7.5).

3. **Interaction design**
   - Collapsible sections (optional).
   - Quick actions or shortcuts (optional).
   - Search or command palette (optional, out of scope for MVP).

4. **Implementation plan**
   - Prioritized list of changes.
   - Dependencies on other tasks (7.4, 7.5).
   - Migration path (no breaking changes for existing users).

---

## Current menu structure (reference)

| Section        | Items                          | Permission gate              |
|----------------|--------------------------------|------------------------------|
| —              | Dashboard                      | All                          |
| —              | Vessels                       | All                          |
| —              | Port Calls                    | All                          |
| Financial      | Disbursement Accounts         | `da:read`                    |
| AI Processing  | Emails, Emissions              | All                          |
| Settings       | Integrations, AI Settings, Billing | `admin:users`, `billing:manage`, `settings:write`, or platform admin |
| Admin          | Users, Roles, Companies       | `admin:users`, `admin:roles`, or platform admin |

---

## Acceptance criteria

### Phase 1 — Analysis

- [ ] Documented inventory of current menu items, sections, and permissions.
- [ ] User journey map for at least 2–3 key workflows.
- [ ] List of identified UX pain points with evidence (heuristic review or user feedback).
- [ ] Brief competitive/pattern research summary.

### Phase 2 — Redesign

- [ ] Proposed information architecture (new structure, groupings).
- [ ] Rationale for changes (why this improves UX).
- [ ] Visual mockup or wireframe (optional but recommended).
- [ ] Implementation checklist with priorities.

### Implementation (if approved)

- [ ] Sidebar updated to new structure.
- [ ] No regression in permission-based visibility.
- [ ] Consistent with Task 7.4 (icon sizing) and Task 7.5 (collapse behavior).

---

## Deliverables

1. **Analysis report** (markdown or doc) — findings, pain points, recommendations.
2. **IA proposal** — new menu structure with rationale.
3. **Implementation task** — follow-up task for dev work (or extend this task).

---

## Related code

- `frontend/src/layout/Sidebar.tsx` — main sidebar, NavItem, SectionDivider
- `frontend/src/layout/AppLayout.tsx` — layout wrapper, mobile menu trigger
- `frontend/src/router.tsx` — route definitions and nesting

---

## Dependencies

- **Task 7.1** — shadcn, Lucide, Tooltip in place.
- **Task 7.3** — Portnomic branding.
- **Task 7.4** — Icon sizing (affects nav item appearance).
- **Task 7.5** — Collapse behavior (affects redesign scope).

---

## Out of scope (for now)

- Global search or command palette (can be a future task).
- Breadcrumb navigation (separate task).
- Mobile-specific menu patterns (drawer vs bottom nav) — focus on desktop sidebar first.
- Changing route URLs (only menu structure and labels).
