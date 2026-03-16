# Task 13.7 — Sync Status Badge & Email Linking UI

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev** and **tailwind-design-system** skills.

---

## Objective

Add Sync Status badge to Port Calls ("Auto-generated" vs "Manual") and allow manual linking of unassigned Emails to a PortCall.

---

## Scope

- **Sync Status badge:** On Port Call list and detail, show badge: "Auto-generated" when `source="ai"`, "Manual" when `source="manual"`.
- **Email linking:** 
  - In Email list/detail: for emails with `port_call_id=null`, show "Link to Port Call" action.
  - Modal or inline: search/select PortCall, then call API to set `email.port_call_id`.
  - API: `PATCH /emails/{id}` or `PUT /emails/{id}` with `port_call_id` (verify endpoint exists).
- Styling: Use existing badge component (e.g. shadcn Badge); distinct colors for Auto vs Manual.

---

## Acceptance criteria

- [ ] Port Call list and detail show Sync Status badge.
- [ ] Unassigned Emails can be linked to a PortCall via UI.
- [ ] Linking updates `email.port_call_id` via API; AuditLog records the change.
