# Task 7.6 — Menu Analysis Report

**Epic:** [07-ux-ui-polish](../epic.md)  
**Task:** [task-06-menu-analysis-redesign.md](./task-06-menu-analysis-redesign.md)

---

## 1. Current Menu Inventory

### 1.1 Nav Items, Sections, and Permissions

| Section | Nav Item | Route | Permission Gate | Primary/Secondary |
|---------|----------|-------|-----------------|-------------------|
| — | Dashboard | `/` | All | Primary |
| — | Vessels | `/vessels` | All | Primary |
| — | Port Calls | `/port-calls` | All | Primary |
| Financial | Disbursement Accounts | `/da` | `da:read` | Primary |
| AI Processing | Emails | `/emails` | All | Primary |
| AI Processing | Emissions | `/emissions` | All | Primary |
| Settings | Integrations | `/settings/integrations` | `admin:users` OR `billing:manage` OR `settings:write` OR `is_platform_admin` | Secondary |
| Settings | AI Settings | `/settings/ai` | `settings:write` OR `is_platform_admin` | Secondary |
| Settings | Billing | `/settings/billing` | `billing:manage` OR `is_platform_admin` | Secondary |
| Admin | Users | `/admin/users` | `admin:users` | Admin |
| Admin | Roles | `/admin/roles` | `admin:roles` | Admin |
| Admin | Companies | `/admin/companies` | `is_platform_admin` only | Admin |

### 1.2 Route and Nested Page Mapping

| Base Route | Nested Routes | Purpose |
|------------|---------------|---------|
| `/` | — | Dashboard (index) |
| `/vessels` | `new`, `:vesselId`, `:vesselId/edit` | List, create, detail, edit |
| `/port-calls` | `new`, `:portCallId`, `:portCallId/edit` | List, create, detail, edit |
| `/da` | `generate`, `:daId` | List, generate, detail |
| `/emails` | `:emailId` | List, detail |
| `/emissions` | `reports/:id` | Dashboard, report detail |
| `/settings/integrations` | — | Integrations page |
| `/settings/ai` | — | AI settings (admin) |
| `/settings/billing` | — | Billing |
| `/admin/users` | `new`, `:userId/edit` | User management |
| `/admin/roles` | `new`, `:roleId/edit` | Role management |
| `/admin/companies` | `new`, `:companyId` | Company management (platform admin) |

### 1.3 Permission Visibility Summary

- **Settings section** appears if user has any of: `admin:users`, `billing:manage`, `settings:write`, or `is_platform_admin`.
- **Admin section** appears if user has any of: `admin:users`, `admin:roles`, or `is_platform_admin`.
- **Financial section** (Disbursement Accounts) appears only with `da:read`.
- **AI Processing** (Emails, Emissions) is visible to all users.

---

## 2. User Journey Maps

### Journey 1: Vessel → Port Call → DA (Operational Workflow)

```
Dashboard → Vessels → Vessel Detail → Port Calls (from vessel) → Port Call Detail → Generate DA → DA Detail
```

| Step | Entry Point | Clicks | Notes |
|------|-------------|--------|-------|
| 1 | Sidebar: Dashboard | 1 | Overview |
| 2 | Sidebar: Vessels | 1 | List view |
| 3 | Vessel row → Vessel Detail | 1 | |
| 4 | "New Port Call" or Port Call row | 1 | From vessel context |
| 5 | Port Call Detail | — | |
| 6 | "Generate Proforma/Final" | 1 | Links to `/da/generate?port_call_id=...` |
| 7 | DA Detail | — | Approve, send |

**Friction points:**
- DA is under "Financial" section; workflow is vessel → port call → DA. Users may not expect DA in a separate section.
- No direct link from Dashboard to DA for users with `da:read`; DA is buried below AI Processing.
- Back links go to list pages (e.g. "Back to Disbursement Accounts"), not to originating port call.

### Journey 2: Email → Parse → Emissions Report (AI Processing Workflow)

```
Emails → Email Detail → Parse with AI → (linked) Emissions Report Detail
```

| Step | Entry Point | Clicks | Notes |
|------|-------------|--------|-------|
| 1 | Sidebar: Emails | 1 | |
| 2 | Email row → Email Detail | 1 | |
| 3 | "Parse with AI" / "Retry parse" | 1 | |
| 4 | Link to Emissions Report (if emission email) | 1 | `/emissions/reports/:id` |

**Friction points:**
- "AI Processing" groups Emails and Emissions; they are related but serve different tasks (inbound parsing vs reporting).
- Emissions is a destination for parsed emission emails; some users may think of it as "reports" rather than "AI."
- No direct path from Emissions dashboard to Emails; users must use sidebar.

### Journey 3: Admin/Settings Configuration

```
Settings: Integrations → AI Settings (if settings:write) → Billing (if billing:manage)
Admin: Users → Roles → Companies (platform admin)
```

| Step | Entry Point | Notes |
|------|-------------|-------|
| 1 | Sidebar: Settings section | Visibility depends on role |
| 2 | Integrations, AI Settings, Billing | Each has its own permission |
| 3 | Admin: Users, Roles, Companies | Admin-only |

**Friction points:**
- Settings section shows if user has *any* of four permissions; individual items may be hidden, causing confusion ("I see Settings but only Integrations").
- Admin and Settings are both "configuration" but split; some users may expect a single "Admin" or "Configuration" area.

---

## 3. UX Pain Points (Heuristic Evidence)

| Pain Point | Heuristic | Evidence |
|------------|-----------|----------|
| **Inconsistent section logic** | Consistency & Standards | First three items (Dashboard, Vessels, Port Calls) have no section; Financial and AI Processing do. Unclear why some are grouped and others not. |
| **"AI Processing" is vague** | Match between system and real world | Emails = inbound parsing; Emissions = reporting/compliance. "AI Processing" describes technology, not user tasks. |
| **Workflow vs. entity mismatch** | Flexibility and efficiency | Core workflow is vessel → port call → DA, but DA is in "Financial" and separated from Port Calls. |
| **Disbursement Accounts jargon** | Match between system and real world | "DA" is industry jargon; some users may not recognize it. Label is clear but long. |
| **Settings visibility confusion** | Visibility of system status | Section appears with mixed permissions; users may not understand why they see some items and not others. |
| **No primary operations section** | Recognition over recall | Dashboard, Vessels, Port Calls are the core operational entities but lack a section label; "Operations" or "Core" would clarify. |
| **Emissions placement** | Consistency | Emissions is both a destination for parsed emails and a standalone reporting area; grouping with Emails under "AI" may obscure its reporting role. |

---

## 4. Competitive / Pattern Research

### B2B SaaS Navigation Patterns

- **Object-oriented vs. workflow-based:** B2B SaaS typically uses object-oriented nav (entities: clients, projects, campaigns) or workflow-based (step-by-step sequences). Maritime agency work is hybrid: entities (vessels, port calls) drive workflows (DA creation, email parsing).
- **Primary items first:** Most-engaged items at top; secondary (Settings, Admin) at bottom. Portnomic follows this but lacks clear primary grouping.
- **Icons + labels:** Icons improve scanability; consistent sizing (Task 7.4) supports this.
- **Section limit:** 3–4 primary sections recommended; current structure has 4 sections (Financial, AI Processing, Settings, Admin) plus ungrouped top items.

### Maritime / Logistics Software

- **Task-oriented design:** Platforms like Windward and Chart Track use modular, task-oriented structures for quick access.
- **Centralized dashboards:** Operations consolidated on single interfaces; Dashboard serves this but nav doesn't reinforce "operations" vs "support" clearly.
- **Customization:** Role-based visibility is common; Portnomic's permission gates align with this.

### Recommendations from Research

1. **Entity-based primary nav** for maritime agencies: Vessels, Port Calls, Disbursement Accounts as core operational entities.
2. **Clear section labels** that match user mental models (Operations, Reports, Settings, Admin).
3. **Limit top-level sections** to avoid cognitive overload.
4. **Consistent hierarchy** for all items (no ungrouped items at top).

---

## 5. Accessibility & Usability Notes

| Area | Current State | Notes |
|------|---------------|-------|
| Keyboard navigation | NavLink supports tab | Ensure focus order follows visual order |
| Screen reader | `aria-label` on collapsed nav items | Good; ensure section labels are announced |
| Touch targets | `py-2`, `px-3` | Adequate; Task 7.4 addresses icon sizing |
| Active state | `bg-oxford-blue-500 text-white` | Clear contrast |
| Focus indicators | Default browser focus | Consider visible focus ring for keyboard users |
| Collapsed state | Tooltip on hover | Aligns with Task 7.5; icons stay in place |

---

## 6. Summary

The current menu has grown organically with mixed grouping logic. Key improvements:

1. **Introduce "Operations" section** for Dashboard, Vessels, Port Calls (and optionally DA) to align with core workflow.
2. **Rename or restructure "AI Processing"** to reflect user tasks (e.g. "Inbox" / "Emails" and "Reports" / "Emissions").
3. **Clarify Financial vs. Operations** — DA is part of the port-call workflow; consider grouping or adjacent placement.
4. **Standardize section visibility** — ensure users understand why they see or don't see items.
5. **Preserve all permission gates** — no regression in role-based visibility.

---

*Next: [task-06-ia-proposal.md](./task-06-ia-proposal.md) for proposed structure and implementation.*
