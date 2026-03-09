# Task 9.4 — Carbon Price API Integration

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Integrate an external API to fetch the current EU carbon (EUA) market price for real-time cost projection in the C-Engine. Cache the price to avoid excessive API calls.

---

## Scope

### API options

- **European Energy Exchange (EEX)** — EUA spot price.
- **ICE (Intercontinental Exchange)** — EU ETS futures.
- **Third-party aggregators** — e.g. CarbonCredits.com, other financial data providers.
- Fallback: configurable default price (env var) when API unavailable.

### Implementation

- **Service:** `CarbonPriceService` — `get_current_price_eur() -> float`.
- **Caching:** Redis or in-memory cache; TTL e.g. 1 hour (prices don't change intraday frequently).
- **Config:** API URL, key (if required), fallback price via env.

### Error handling

- On API failure: use cached value if fresh; else use fallback; log warning.
- Do not block emission calculation — always return a price (cached or fallback).

---

## Acceptance criteria

- [ ] Carbon price is fetched from external API (or cached/fallback).
- [ ] C-Engine uses live price for EUA cost projection when available.
- [ ] Failures degrade gracefully (cache/fallback) without breaking the flow.

---

## Related code

- `backend/app/services/carbon_price.py` — new service
- `backend/app/config.py` — CARBON_PRICE_API_URL, FALLBACK_CARBON_PRICE_EUR

---

## Dependencies

- Redis (if using for cache) — Epic 2/5.
- External API account/key if required.
