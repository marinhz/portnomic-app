# Strategic Specification: Bring Your Own AI (BYOAI)

**Project:** ShipFlow AI  
**Module:** Self-Service AI Integration & Prompt Management  
**Target:** Premium plans (Professional, Enterprise)

---

## 1. Executive summary

ShipFlow currently uses a **platform-level** LLM API key for all AI parsing (email, DA, emissions). This creates:

- **Recurring cost** — Every parse consumes tokens billed to ShipFlow.
- **Limited control** — Tenants cannot tune prompts or choose providers.
- **Compliance friction** — Enterprises may require their own keys for data residency or audit.

**BYOAI** lets company admins configure their own API keys and manage parsing prompts. ShipFlow incurs no AI cost for those tenants. This is a **premium-only** feature, aligning cost avoidance with higher-tier value.

---

## 2. Strategic rationale

### 2.1 Cost avoidance

| Scenario | Today | With BYOAI |
|----------|-------|------------|
| 100 parses/month, $0.01/parse | $1.00 ShipFlow cost | $0 (tenant pays) |
| 10,000 parses/month | $100 ShipFlow cost | $0 (tenant pays) |

As usage grows, platform AI spend grows linearly. BYOAI shifts that cost to tenants who opt in.

### 2.2 Enterprise appeal

- **Data sovereignty** — Tenant’s key → tenant’s data flow; no shared platform key.
- **Audit** — Tenant can see usage in their own provider dashboard.
- **Provider choice** — OpenAI, Azure OpenAI, local models (OpenAI-compatible API).

### 2.3 Premium differentiation

- **Starter** — Uses platform key (if configured); limited parse quota.
- **Professional / Enterprise** — Can bring own key; unlimited or higher parse quota; custom prompts.

---

## 3. Functional requirements

### 3.1 Tenant LLM configuration

- **Fields:** `api_key` (encrypted), `base_url`, `model`, `enabled`.
- **Storage:** Per-tenant; encrypted at rest (e.g. Fernet, AES).
- **Validation:** Optional “test connection” to verify key works.

### 3.2 Prompt management

- **Parser types:** `da_email`, `emission_report`.
- **Per-type:** Custom prompt text; version; “reset to default”.
- **Schema:** Prompts must instruct JSON output; basic validation on save.

### 3.3 Routing logic

1. If tenant has BYOAI config and `enabled` → use tenant key/URL/model.
2. Else if platform has default key → use platform key (current behavior).
3. Else → fail with clear error (“Configure AI settings or contact support”).

### 3.4 Feature gating

- **Access:** Only `professional` and `enterprise` plans can configure BYOAI.
- **UI:** Non-premium users see upgrade CTA.
- **API:** 403 with `upgrade_required` when non-premium tenant tries to set config.

---

## 4. Security considerations

- API keys never returned in API responses (masked: `sk-...xxxx`).
- Keys encrypted with tenant-scoped or platform secret.
- Audit log: “AI config updated” (no key value).
- Admin-only: Only company admins can view/edit.

---

## 5. UI/UX outline

### Settings → AI Integration (premium only)

- API key input (password field, masked).
- Base URL (default: OpenAI).
- Model (dropdown or free text).
- “Test connection” button.
- Save / Clear.

### Settings → AI Prompts (premium only)

- Tabs or list: DA Email Parser, Emission Parser.
- Text area for prompt.
- “Reset to default” button.
- Save.

---

## 6. Out of scope (v1)

- Usage metering (tokens per tenant).
- Multiple providers per tenant.
- Prompt templates marketplace.
- A/B testing of prompts.
