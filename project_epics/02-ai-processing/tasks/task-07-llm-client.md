# Task 2.7 — LLM client (OpenAI-compatible, pluggable)

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Pluggable LLM client calling an OpenAI-compatible API; configurable URL and key; timeouts and retries (EDD §8.2, §8.3).

## Scope

- Client interface: accept prompt (or messages), output schema/format; return structured JSON.
- Configuration: LLM_API_URL, LLM_API_KEY (or equivalent) from env/secret manager.
- Timeouts and retries (e.g. 3 with backoff) for transient errors (EDD §8.3).
- Support structured output (e.g. JSON mode) per provider.

## Acceptance criteria

- [ ] Worker can call LLM with prompt and receive structured response; config is externalized.
- [ ] Timeouts and retries are applied; failures are distinguishable (transient vs permanent).
- [ ] Swapping provider (same API shape) does not require code change beyond config.
