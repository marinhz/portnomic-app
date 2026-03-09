# Task 4.7 — GDPR: data export (access/portability)

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Export of user and operational data (e.g. JSON/CSV) via secure download for right of access and portability (EDD §13, FR-9).

## Scope

- **Scope:** User's own profile; operational data accessible to user (e.g. vessels, port calls, DAs within tenant); format JSON and/or CSV.
- **Endpoint or UI:** Authenticated request; generate export (async if large); secure download link (time-limited, signed) or inline response.
- **Security:** Only data the requesting user is entitled to; no other tenants' data; rate limit on export requests.
- Document what is included in export and how to request it.

## Acceptance criteria

- [ ] User (or admin on behalf of user) can request export; receives data they are entitled to in machine-readable format.
- [ ] Export is secure (auth, scope, link expiry); no cross-tenant data.
- [ ] Process is documented for compliance (EDD §13).
