# Task 10.5 — Admin AI Settings UI (Keys & Prompts)

**Epic:** [10-bring-your-own-ai](../epic.md)  
**Parent:** [Task 10.4 — Admin AI settings API](task-04-admin-ai-settings-api-feature-gating.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

Build Settings → AI Integration and Settings → AI Prompts pages. Company admins can configure API key, base URL, model, and customize parsing prompts. Non-premium users see upgrade CTA.

---

## Scope

### 1. Route structure

- `/settings/ai` — AI Integration (API key, base URL, model).
- `/settings/ai/prompts` — AI Prompts (DA parser, Emission parser).

Or combined: `/settings/ai` with tabs for "Integration" and "Prompts".

### 2. AI Integration page

- **API Key** — Password input; placeholder "Enter new key to update" when already configured.
- **Base URL** — Text input; default "https://api.openai.com/v1"; help text for Azure/other.
- **Model** — Text input or select; default "gpt-4o-mini".
- **Test connection** — Button; call `POST /settings/ai/test`; show success/error toast.
- **Save** — Submit form; success toast.
- **Clear / Remove** — Optional; remove config with confirmation.

### 3. AI Prompts page

- **Parser types:** DA Email Parser, Emission Parser.
- For each: large text area with current prompt; "Reset to default" button; Save.
- Show version if available.

### 4. Upgrade CTA (non-premium)

- If 403 `upgrade_required` on load or save: show banner/card with "Upgrade to Professional or Enterprise to configure your own AI settings" and link to billing/plans.

### 5. Access control

- Only company admins see these routes (or redirect with message).
- Match backend permission checks.

### 6. Design

- Use existing Settings layout (e.g. sidebar or tabs from Settings).
- Shadcn components: Input, Button, Card, Tabs, Textarea, Alert.
- Consistent with Epic 7 (UX polish).

---

## Acceptance criteria

- [ ] AI Integration page: configure key, URL, model; test connection; save.
- [ ] AI Prompts page: edit prompts for DA and Emission; reset to default.
- [ ] Non-premium users see upgrade CTA.
- [ ] Non-admin users cannot access (redirect or 403 handling).
- [ ] Forms validate; errors displayed clearly.

---

## Related code

- `frontend/src/pages/settings/` — new or extend
- `frontend/src/routes/` — add settings/ai routes
- API client for `/settings/ai` endpoints

---

## Dependencies

- Task 10.4 — API endpoints exist
- Epic 7 — Shadcn, design system
