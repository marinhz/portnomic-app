# ShipFlow AI — Project Epics

Epics derived from the **Implementation Roadmap** in [SHIPFLOW_AI_Engineering_Design_Document.md](../SHIPFLOW_AI_Engineering_Design_Document.md).

| # | Epic | Folder | Duration |
|---|------|--------|----------|
| 1 | Core infrastructure (DB, auth, tenant, RBAC, base API & frontend shell) | [01-core-infrastructure](01-core-infrastructure/epic.md) | 2 weeks |
| 2 | AI processing (email ingest, queue, LLM, parse job, persist to port call) | [02-ai-processing](02-ai-processing/epic.md) | 3 weeks |
| 3 | Financial automation (tariffs, DA formula engine, Proforma/Final DA, PDF, dispatch, approval) | [03-financial-automation](03-financial-automation/epic.md) | 3 weeks |
| 4 | Beta & security (pen test, audit review, GDPR checks, performance tuning) | [04-beta-security](04-beta-security/epic.md) | 2 weeks |
| 5 | Production rollout (go-live, monitoring, runbooks, support handover) | [05-production-rollout](05-production-rollout/epic.md) | Ongoing |
| 6 | Email connection (OAuth 2.0 for Gmail/Outlook, per-tenant mailbox, Settings/Integrations UI) | [06-email-connection-oauth](06-email-connection-oauth/epic.md) | 3–4 weeks |
| 7 | UX & UI polish (shadcn/ui, Lucide icons, Sonner toasts) | [07-ux-ui-polish](07-ux-ui-polish/epic.md) | 1–2 weeks |
| 8 | Business & monetization (subscription, Stripe, feature gating) | [08-business-monetization](08-business-monetization/epic.md) | 3–4 weeks |
| 9 | Eco-compliance & emissions (AI extraction, C-Engine, EU ETS, MRV export) | [09-emicion-epic](09-emicion-epic/epic.md) | 4–5 weeks |
| 10 | Bring Your Own AI (BYOAI) — tenant API keys & prompt management, premium only | [10-bring-your-own-ai](10-bring-your-own-ai/epic.md) | 3–4 weeks |

Each epic folder contains:
- **epic.md** — Objective, scope, acceptance criteria, and EDD section references.
- **tasks/** — Task files derived from the epic (see each epic’s `tasks/README.md` for the list).
