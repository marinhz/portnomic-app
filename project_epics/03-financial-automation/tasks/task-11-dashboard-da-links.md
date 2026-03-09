# Task 3.11 — Dashboard and port call links to DA

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Dashboard and port call views link to DA list and DA generation so users can navigate to DAs and create new ones (EDD §4.1).

## Scope

- **Dashboard:** Section or link "Disbursement accounts"; list DAs (e.g. by port call, status); link to DA workspace.
- **Port call detail:** List DAs for this port call; button "Generate Proforma" / "Generate Final DA"; link to DA workspace.
- Optional: DA list filters (status, port call, date range); pagination.
- Consistent with RBAC (da:read, da:write).

## Acceptance criteria

- [ ] User can reach DA list from dashboard and from port call; can open a DA in workspace.
- [ ] Generate from port call creates DA and navigates to it (or shows in list); filters work as designed.
- [ ] No access to other tenants' DAs; 403 handled in UI.
