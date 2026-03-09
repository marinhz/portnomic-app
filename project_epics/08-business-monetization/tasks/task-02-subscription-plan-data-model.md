# Task 8.2 — Subscription Plan Data Model and Migration

**Epic:** [08-business-monetization](../epic.md)  
**Parent:** [Task 8.1 — Monetization plan](task-01-monetization-plan-and-implementation.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills. This task involves models, migrations, config constants, and schema design — core Backend responsibilities.

---

## Objective

Add subscription plan and billing fields to the Tenant (or Company) model and create the plan limits configuration so the system can track and enforce plan-based limits.

---

## Scope

### 1. Subscription plan enum or table

- Add `subscription_plan` enum: `starter`, `professional`, `enterprise`.
- Or: small lookup table `subscription_plans` with plan key and display name.

### 2. Tenant model changes

Add to Tenant (or Company):

| Column | Type | Notes |
|--------|------|-------|
| `plan` | enum / FK | `starter`, `professional`, `enterprise` |
| `subscription_status` | enum | `active`, `trial`, `canceled`, `past_due` |
| `stripe_customer_id` | str, nullable | Stripe customer ID |
| `stripe_subscription_id` | str, nullable | Stripe subscription ID |

- Default: `plan = starter`, `subscription_status = trial` (or `active` for existing tenants).

### 3. Plan limits config

Add `plan_limits` config (in `config.py` or constants):

```python
PLAN_LIMITS = {
    "starter": {"users": 3, "vessels": 10, "das_per_month": 50, "ai_parses_per_month": 100},
    "professional": {"users": 10, "vessels": 50, "das_per_month": 200, "ai_parses_per_month": 500},
    "enterprise": {"users": None, "vessels": None, "das_per_month": None, "ai_parses_per_month": None},
}
```

- `None` = unlimited.

### 4. Usage counters (optional in this task)

- Option A: Add `das_count_current_month`, `ai_parses_count_current_month` to Tenant (reset monthly).
- Option B: Defer to Task 8.4 — compute from existing tables (e.g. count DAs created this month).
- **Recommendation:** Defer counters to Task 8.4; this task focuses on schema and config.

### 5. Alembic migration

- Create migration for new columns.
- No destructive changes to existing data.
- Backfill existing tenants with default plan (`starter`) and status (`active` or `trial`).

---

## Acceptance criteria

- [ ] Migration adds `plan`, `subscription_status`, `stripe_customer_id`, `stripe_subscription_id` to Tenant.
- [ ] `PLAN_LIMITS` config exists and is used by limits service (or placeholder).
- [ ] Existing tenants have sensible defaults after migration.
- [ ] Model and schemas expose plan and subscription_status for API responses.

---

## Related code

- `backend/app/models/tenant.py` — add subscription fields
- `backend/app/config.py` — add `PLAN_LIMITS` constant
- `backend/alembic/versions/` — new migration

---

## Dependencies

- Task 1.20 (Multitenant companies) — Tenant model exists
