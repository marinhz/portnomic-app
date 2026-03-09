# Epic 10 — Bring Your Own AI (BYOAI) & Prompt Management

**Source:** Strategic — Cost avoidance, enterprise flexibility, premium differentiation  
**Duration (estimate):** 3–4 weeks

---

## Agent assignments

| Task | Agent | Skills |
|------|-------|--------|
| 10.1 Tenant LLM config data model | Backend | fastapi-python, python-project-structure |
| 10.2 API key storage & encryption | Backend | fastapi-python |
| 10.3 LLM client tenant-aware routing | Backend | fastapi-python |
| 10.4 Admin AI settings API & feature gating | Backend | fastapi-python |
| 10.5 Admin AI settings UI (keys & prompts) | Frontend | react-dev, react-router-v7, tailwind-design-system |

---

## Strategic objective

**Eliminate ShipFlow’s AI API costs** by letting premium customers bring their own API keys. Company admins configure and manage their own LLM credentials and parsing prompts. This reduces platform spend, improves enterprise control, and differentiates premium tiers.

---

## Scope

### Bring Your Own API Key (BYOAI)

- **Per-tenant LLM config** — API key, base URL, model (OpenAI-compatible).
- **Encrypted storage** — API keys stored encrypted at rest; never logged or exposed in responses.
- **Fallback** — If tenant has no config, use platform default (if configured); otherwise return clear error.
- **Premium only** — Feature gated to Professional and Enterprise plans.

### Prompt management

- **Custom prompts per tenant** — Admins can override default prompts for:
  - DA / disbursement email parsing
  - Noon / bunker report (emission) parsing
- **Versioning** — Track prompt version; support “reset to default”.
- **Validation** — Basic schema validation (e.g. required JSON output instructions).

### Admin UI

- **Settings → AI Integration** — Configure API key, base URL, model.
- **Settings → AI Prompts** — View/edit prompts for each parser type; reset to default.
- **Visibility** — Only company admins (or equivalent role) can access.

---

## Out of scope (for this epic)

- Usage metering per tenant (e.g. token counts) — future enhancement.
- Multiple LLM providers per tenant (e.g. OpenAI + Anthropic) — single provider per tenant.
- Prompt A/B testing or analytics — future enhancement.

---

## Acceptance criteria

- [ ] Tenant can store encrypted LLM API key, base URL, and model; only premium plans can configure.
- [ ] Parse workers use tenant’s config when available; fallback to platform default.
- [ ] Admins can customize prompts for DA and emission parsing; reset to default supported.
- [ ] Admin UI for AI settings and prompts; restricted to company admins.
- [ ] Non-premium tenants see upgrade CTA when attempting to access AI settings.

---

## Dependencies

- Epic 8 (Business & Monetization) — Plan tiers, feature gating, limits service.
- Epic 2 (AI processing) — LLM client, parse worker, prompts.
- Epic 9 (Emissions) — Emission parser and prompts.
- Role/permission model for “company admin” (Epic 1).

---

## Business value

| Aspect | Benefit |
|--------|---------|
| **Cost** | No AI API spend for tenants with BYOAI; scales with adoption. |
| **Enterprise** | Companies control their own keys, compliance, and data residency. |
| **Premium** | Strong differentiator for Professional/Enterprise plans. |
| **Flexibility** | Custom prompts improve parsing accuracy for niche formats. |
