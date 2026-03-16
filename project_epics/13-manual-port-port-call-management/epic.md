# Epic 13 — Manual Port & Port Call Management UI

**Duration (estimate):** 2–3 weeks

---

## Context

The current implementation relies heavily on AI ingestion for Port and Port Call creation. This epic provides a **manual fallback** so users can manage Ports and create Port Calls manually, ensuring 100% system usability when AI parsing is unavailable, incomplete, or when users prefer direct data entry.

---

## Strategic objective

Enable full operational capability without AI dependency: users can maintain a Port Directory, create Port Calls from scratch, and link unassigned email threads to manually created Port Calls. All manual actions are audited identically to AI-generated ones.

---

## Scope

### 2.1 Port Management UI

| Item | Specification |
|------|---------------|
| **Route** | `/dashboard/directory/ports` (or `/directory/ports` under app layout) |
| **List** | Searchable list of all Ports in the tenant |
| **Add Port modal** | Fields: `Name`, `Country`, `UN/LOCODE`, `Coordinates`, `Timezone` |
| **Tariff link** | Per-port link to Tariff Configuration (existing tariff routes) |

**Data model notes:**

- Port entity already has: `name`, `code` (maps to UN/LOCODE), `country`, `timezone`.
- **Coordinates** may require schema extension (e.g. `latitude`, `longitude` or `coordinates` JSONB).

### 2.2 Manual Port Call Creation

| Item | Specification |
|------|---------------|
| **Route** | `/dashboard/port-calls/new` (or `/port-calls/new`) |
| **Flow** | Multi-step wizard: |
| Step 1 | Search/Select **Vessel** (from existing vessels table) |
| Step 2 | Search/Select **Port** (from Port Directory) |
| Step 3 | Input **ETA**, **ETD**, **Agent Assigned** |
| **Audit** | Manual entries trigger same `AuditLog` events as AI-generated ones |

**Data model notes:**

- PortCall entity has: `vessel_id`, `port_id`, `eta`, `etd`, `status`.
- **Agent Assigned** may require schema extension (e.g. `agent_assigned` string or FK to User).
- **Source tracking** (manual vs auto-generated) required for Sync Status badge.

### 2.3 UX Improvements

| Item | Specification |
|------|---------------|
| **Sync Status badge** | Display on Port Calls: "Auto-generated" vs "Manual" |
| **Email linking** | Allow manual linking of an unassigned Email thread to a manually created PortCall |

**Implementation notes:**

- PortCall needs `source` or `created_via` field: `"ai"` | `"manual"`.
- Email entity has nullable `port_call_id`; linking UI updates `email.port_call_id` via API.

---

## Agent assignments

| Task | Agent | Skills |
|------|-------|--------|
| 13.1 Port schema extension (coordinates, UN/LOCODE alias) | Backend | fastapi-python, python-project-structure |
| 13.2 PortCall schema extension (agent_assigned, source) | Backend | fastapi-python, python-project-structure |
| 13.3 Port Directory API (list with search, CRUD) | Backend | fastapi-python |
| 13.4 Port Directory UI (`/directory/ports`) | Frontend | react-dev, react-router-v7, tailwind-design-system |
| 13.5 Manual Port Call wizard UI (`/port-calls/new`) | Frontend | react-dev, react-router-v7, tailwind-design-system |
| 13.6 AuditLog parity for manual Port/PortCall actions | Backend | fastapi-python |
| 13.7 Sync Status badge & Email linking UI | Frontend | react-dev, tailwind-design-system |
| 13.8 Tariff Management UI | Frontend | react-dev, tailwind-design-system |

---

## Out of scope (for this epic)

- AI ingestion changes; this epic is additive.
- Bulk import of Ports (CSV/Excel).
- Port Call templates or recurring patterns.
- Automated agent assignment logic.

---

## Acceptance criteria

- [ ] Port Directory at `/directory/ports` shows searchable list of all tenant Ports.
- [ ] "Add Port" modal supports Name, Country, UN/LOCODE, Coordinates, Timezone.
- [ ] Each Port row links to Tariff Configuration.
- [ ] Manual Port Call creation at `/port-calls/new` uses 3-step wizard: Vessel → Port → ETA/ETD/Agent.
- [ ] Manual Port and PortCall create/update actions are logged in AuditLog with same structure as AI-generated ones.
- [ ] Port Calls display Sync Status badge: "Auto-generated" or "Manual".
- [ ] Unassigned Emails can be manually linked to a PortCall from the UI.

---

## Dependencies

- Epic 1 (Core infrastructure) — Port, PortCall, Vessel, Email entities; AuditLog; RBAC.
- Epic 2 (AI processing) — Email entity, parse worker (for contrast with manual flow).
- Epic 3 (Financial automation) — Tariff entity, Tariff Configuration routes.
- Epic 7 (UX polish) — shadcn/ui, design system.

---

## Business value

| Aspect | Benefit |
|--------|---------|
| **Resilience** | System remains fully usable when AI is down or not configured. |
| **User control** | Operators can correct or pre-empt AI by entering data manually. |
| **Compliance** | Manual actions are audited; no gap vs AI-generated records. |
| **Email traceability** | Unassigned emails can be linked to Port Calls for full audit trail. |
