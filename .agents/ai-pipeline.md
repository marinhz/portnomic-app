# AI Pipeline Agent — ShipFlow AI

Applies to email ingestion, LLM integration, parse jobs, structured output, and worker-side AI processing.

## Flow

1. **Ingest** — Email received (IMAP or webhook); persist with `processing_status = pending`.
2. **Enqueue** — Job to Redis/queue with `email_id`, `tenant_id`.
3. **Worker** — Pick job; load email; call LLM with versioned prompt + output schema.
4. **Parse** — LLM returns structured JSON (vessel ref, port, dates, line items, amounts, currency).
5. **Validate** — Schema validation and business rules (currency, date range).
6. **Persist** — Map to entities (create/update PortCall, attach parsed data to Email); set `processing_status = completed` or `failed`.
7. **Notify** — Optional webhook or event for UI refresh.

## Integration

- **LLM:** Pluggable OpenAI-compatible API; sync or async with timeouts and retries.
- **Idempotency:** `email_id` as idempotency key; duplicate jobs must not overwrite.
- **Output schema:** Versioned JSON schema for vessel, port, dates, `line_items[]` (description, amount, currency).

## Failure Handling

- Retries (e.g. 3) with backoff for transient LLM/network errors.
- After max retries: mark email `failed`, store error reason, alert.
- Support manual override: operator can correct parsed data or mark invalid.

## Conventions

- Prompts and output schema versioned and stored (e.g. in repo or config).
- No raw PII or full email bodies in logs; use correlation_id and job id for tracing.
- Worker must respect tenant isolation when reading/writing DB.
