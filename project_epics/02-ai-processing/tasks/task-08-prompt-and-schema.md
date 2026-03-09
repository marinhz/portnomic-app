# Task 2.8 — Prompt and output schema (versioned)

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Versioned prompt template and JSON output schema for maritime email parsing: vessel ref, port, dates, line_items[] (description, amount, currency) (EDD §8.1, §8.2).

## Scope

- **Prompt:** Template with instructions, optional few-shot examples, and output format; version stored (e.g. in repo or config).
- **Output schema:** JSON schema for parsed result: vessel ref, port, dates, line_items array (description, amount, currency).
- Version identifier so worker and API can reference which prompt/schema was used.
- Validation of LLM output against schema before persist.

## Acceptance criteria

- [ ] Worker loads prompt and schema by version; sends to LLM and validates response.
- [ ] Invalid or malformed output is caught; email can be marked failed with reason.
- [ ] Schema supports vessel, port, dates, and line items with required fields.
