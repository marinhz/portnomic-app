# Task 7.6 — Information Architecture Proposal

**Epic:** [07-ux-ui-polish](../epic.md)  
**Task:** [task-06-menu-analysis-redesign.md](./task-06-menu-analysis-redesign.md)  
**Analysis:** [task-06-analysis-report.md](./task-06-analysis-report.md)

---

## 1. Proposed Menu Structure

### 1.1 New Structure (Visual)

```
┌─────────────────────────────────────┐
│ Portnomic                           │
├─────────────────────────────────────┤
│ Operations                          │
│   Dashboard                         │
│   Vessels                           │
│   Port Calls                        │
│   Disbursement Accounts  [da:read]   │
├─────────────────────────────────────┤
│ Inbox & Reports                     │
│   Emails                            │
│   Emissions                         │
├─────────────────────────────────────┤
│ Settings          [admin|billing|   │
│   Integrations     settings|platform]│
│   AI Settings     [settings:write]  │
│   Billing         [billing:manage]   │
├─────────────────────────────────────┤
│ Admin            [admin:users|roles| │
│   Users           platform]          │
│   Roles                             │
│   Companies       [platform admin]   │
└─────────────────────────────────────┘
```

### 1.2 Section-by-Section Rationale

| Section | Items | Rationale |
|---------|-------|-----------|
| **Operations** | Dashboard, Vessels, Port Calls, Disbursement Accounts | Core operational workflow: vessel → port call → DA. Grouping DA with Port Calls supports the primary user journey. DA is permission-gated but logically belongs here. |
| **Inbox & Reports** | Emails, Emissions | Task-oriented: Emails = inbound processing/inbox; Emissions = reporting. Replaces vague "AI Processing" with user-facing language. |
| **Settings** | Integrations, AI Settings, Billing | Configuration and account management. Same permission logic as today. |
| **Admin** | Users, Roles, Companies | Tenant and platform administration. Unchanged. |

---

## 2. Task-Based vs. Entity-Based Decision

**Decision: Entity-based primary structure with task-oriented labels.**

- **Operations** is entity-based: Vessels, Port Calls, Disbursement Accounts are the core entities maritime agencies work with daily.
- **Inbox & Reports** is task-oriented: "Emails" = process incoming mail; "Emissions" = view reports.
- **Settings** and **Admin** are standard B2B patterns (configuration vs. user/tenant management).

This hybrid approach matches maritime agency mental models: they think in terms of vessels and port calls first, then supporting tasks (email parsing, emissions reporting).

---

## 3. Visual Hierarchy

### 3.1 Section Dividers

- Use existing `SectionDivider` component.
- Collapsed state: horizontal rule only (no label).
- Expanded state: uppercase, small, muted label (e.g. `text-[11px] font-semibold uppercase tracking-wider text-oxford-blue-500`).

### 3.2 Spacing

- `space-y-1` between nav items within a section.
- `pt-4 pb-1` above each section divider (existing).
- No extra spacing between sections beyond divider padding.

### 3.3 Collapsible Sections

**Out of scope for MVP.** Current flat list with dividers is sufficient. Collapsible sections add complexity and may reduce discoverability for infrequent items. Revisit if the menu grows significantly (e.g. 15+ items).

### 3.4 Alignment with Task 7.4 and 7.5

- **Icon sizing:** Nav icons remain `size-5` (Task 7.4).
- **Collapse behavior:** Icons stay in same position when collapsed; only labels hidden (Task 7.5).
- **Tooltips:** Collapsed nav items show label on hover.

---

## 4. Changes Summary

| Change | Before | After |
|--------|--------|-------|
| Top items | No section (Dashboard, Vessels, Port Calls) | **Operations** section |
| DA placement | Financial section, after Port Calls | **Operations** section, after Port Calls |
| AI Processing | Section label | **Inbox & Reports** |
| Financial | Section label | Removed (DA moved to Operations) |

---

## 5. Implementation Checklist

### Priority 1 (Must Have)

- [x] Add **Operations** section with Dashboard, Vessels, Port Calls.
- [x] Move Disbursement Accounts into Operations (after Port Calls), keep `da:read` gate.
- [x] Rename **AI Processing** to **Inbox & Reports**.
- [x] Remove **Financial** section (DA no longer in it).
- [x] Preserve all permission gates (no regression).

### Priority 2 (Verify)

- [x] Confirm SectionDivider spacing matches Task 7.4 icon/divider standards.
- [x] Confirm collapsed state: divider shows horizontal rule only.
- [x] Test with different permission sets: no DA, no Settings items, no Admin items, platform admin.

### Priority 3 (Optional)

- [ ] Add `aria-label` or `aria-labelledby` for nav sections if screen reader testing reveals gaps.
- [ ] Document new structure in task for future reference.

---

## 6. Migration Notes

- **No URL changes** — routes unchanged.
- **No breaking changes** — only menu order and section labels change.
- **Permission logic** — identical to current implementation; copy existing `hasDARead`, `showSettings`, `showAdmin` logic.

---

## 7. Approval

If this proposal is approved, proceed to update `Sidebar.tsx` per the implementation checklist.
