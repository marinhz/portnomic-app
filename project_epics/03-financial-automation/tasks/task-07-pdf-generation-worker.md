# Task 3.7 — PDF generation worker

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Generate DA as PDF from template (e.g. HTML → PDF); store in object storage; set pdf_blob_id on DA record (EDD §9.3, §7.4).

## Scope

- Worker task: input DA id; load DA (and port call, vessel, port for template); render template with DA data and branding; generate PDF (WeasyPrint, wkhtmltopdf, or headless Chrome).
- Upload PDF to object storage (config: STORAGE_*); get blob id/URL; update DA.pdf_blob_id.
- Triggered by API (POST /da/{id}/send) or separate "generate PDF only" if needed.
- Timeouts and retries; failure does not transition DA to sent.

## Acceptance criteria

- [ ] PDF is generated and stored; DA record updated with pdf_blob_id.
- [ ] Template supports DA line items, totals, and branding; output is readable and correct.
- [ ] Failures are logged and do not corrupt DA state; can retry.
