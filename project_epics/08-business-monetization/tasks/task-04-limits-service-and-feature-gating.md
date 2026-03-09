# Task 8.4 — Limits Service and Feature Gating

**Epic:** [08-business-monetization](../epic.md)  
**Parent:** [Task 8.1 — Monetization plan](task-01-monetization-plan-and-implementation.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills. This task involves services, dependency injection, HTTPException patterns, and integration across user/vessel/DA/parse routers — core Backend work.

---

## Objective

Implement a limits service that checks tenant usage against plan limits and enforce feature gating before user creation, vessel creation, DA generation, and AI parsing. Return 403 with upgrade message when over limit.

---

## Scope

### 1. Limits service

- `backend/app/services/limits.py`
- `check_user_limit(db, tenant_id) -> bool` — returns True if under limit.
- `check_vessel_limit(db, tenant_id) -> bool`
- `check_da_limit(db, tenant_id) -> bool` — DAs created this month vs `das_per_month`.
- `check_ai_parse_limit(db, tenant_id) -> bool` — AI parses this month vs `ai_parses_per_month`.
- Or: `check_limit(db, tenant_id, limit_type: Literal["users","vessels","das","ai_parse"]) -> bool`
- Uses `PLAN_LIMITS` from config; `None` = unlimited.

### 2. Integration points

| Action | Where to check | Limit type |
|--------|----------------|------------|
| User create | User service / router | users |
| Vessel create | Vessel service / router | vessels |
| DA generate | DA service / router | das_per_month |
| AI parse | Parse service / email ingest | ai_parses_per_month |

- Call `check_*_limit` before performing the action.
- If `False`: raise `HTTPException(403, detail={"code": "upgrade_required", "message": "..."})`.

### 3. Usage counters

- **Users:** `SELECT COUNT(*) FROM users WHERE tenant_id = ?`
- **Vessels:** `SELECT COUNT(*) FROM vessels WHERE tenant_id = ?`
- **DAs this month:** `SELECT COUNT(*) FROM disbursement_accounts WHERE tenant_id = ? AND created_at >= start_of_month`
- **AI parses this month:** Count from ParseJob or equivalent where `created_at >= start_of_month` and `tenant_id = ?`

- Add indexes if needed for efficient monthly counts.

### 4. Monthly reset

- **Option A:** No stored counter — always compute from DB (simplest).
- **Option B:** Stored counters on Tenant; scheduled job (cron/celery) resets `das_count_current_month`, `ai_parses_count_current_month` on 1st of month.
- **Recommendation:** Option A for MVP; add Option B if counts become slow.

### 5. API error response

- When over limit: `403 Forbidden` with body:
  ```json
  {
    "detail": {
      "code": "upgrade_required",
      "message": "User limit reached. Upgrade your plan to add more users.",
      "limit_type": "users"
    }
  }
  ```

---

## Acceptance criteria

- [ ] `limits_svc.check_user_limit` (and vessel, DA, AI parse) implemented.
- [ ] User creation blocked when at plan user limit; returns 403 with `upgrade_required`.
- [ ] Vessel creation blocked when at plan vessel limit.
- [ ] DA generation blocked when over monthly DA limit.
- [ ] AI parse blocked or throttled when over monthly parse limit.
- [ ] Enterprise plan: all limits return True (unlimited).

---

## Implementation notes

### Example limit check

```python
async def check_user_limit(db, tenant_id: UUID) -> bool:
    plan = await get_tenant_plan(db, tenant_id)
    limit = PLAN_LIMITS[plan].get("users")
    if limit is None:
        return True
    count = await count_users(db, tenant_id)
    return count < limit
```

### Dependency injection

- Create `require_under_limit(limit_type)` dependency that raises 403 if over limit.
- Or: call `check_*_limit` at start of each create/generate handler.

---

## Related code

- `backend/app/services/limits.py` — new service
- `backend/app/services/user_svc.py` — add limit check before create
- `backend/app/services/vessel_svc.py` — add limit check before create
- `backend/app/services/` — DA and parse services
- `backend/app/config.py` — `PLAN_LIMITS`

---

## Dependencies

- Task 8.2 (Subscription plan data model) — plan and limits config exist
