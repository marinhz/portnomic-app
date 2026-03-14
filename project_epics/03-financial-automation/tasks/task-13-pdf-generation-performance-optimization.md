# Task 3.13 — PDF Generation Performance & Optimization

**Epic:** [03-financial-automation](../epic.md)

---

## Agent

Use the **Backend** agent for PDF service changes; research and benchmarking can use shell/explore agents.

---

## Problem

DA PDF generation is too slow. Users experience long waits when generating or sending Disbursement Account PDFs. The current implementation uses WeasyPrint (HTML → PDF), which is known for slow rendering and poor scaling.

---

## Research summary (2024–2025)

### Current stack

- **Library:** WeasyPrint ≥62.0 (`backend/app/services/pdf_generator.py`)
- **Usage:** DA PDFs + EU MRV export (`emission_export.py`)
- **Flow:** HTML template → `HTML(string=html).write_pdf()` → bytes

### Benchmark data (1-page documents)

| Library      | 1-page time | 500-page (bulk) | Notes                            |
|-------------|-------------|------------------|----------------------------------|
| FPDF2       | ~50 ms      | —                | Pure Python, minimal deps       |
| ReportLab   | ~80 ms      | —                | Strong for tables, financial docs|
| WeasyPrint  | ~335 ms     | 8.7 s (17 ms/pg) | HTML/CSS, heavy; poor scaling    |
| Playwright  | ~750 ms     | —                | Browser-based, high memory       |
| PDFKit/wkhtmltopdf | ~650 ms | —         | Wraps external binary           |

### WeasyPrint-specific issues

- **CSS Grid:** [Issue #2336](https://github.com/Kozea/WeasyPrint/issues/2336) — switching from `display: grid` to `display: flex` or tables can reduce generation time from ~13 s to ~1 s on complex layouts.
- **Large documents:** Users report 40+ minutes for 50 MB HTML, 2+ hours for 100 MB.
- **Dependencies:** Cairo, Pango, GTK — heavy system libraries; harder to deploy (Docker, CI).

### Alternatives to evaluate

| Option        | Pros                                   | Cons                                  |
|---------------|----------------------------------------|---------------------------------------|
| **ReportLab** | Fast, mature, great tables, no browser | No HTML; programmatic API only        |
| **FPDF2**     | Very fast, lightweight, simple         | Limited layout; no HTML/CSS           |
| **wkhtmltopdf/PDFKit** | HTML input, familiar      | External binary, 650 ms baseline       |
| **Typst** (subprocess) | 0.3 ms/page after startup       | New templating system to learn         |
| **Playwright** | Pixel-perfect HTML/CSS/JS              | Slow (~750 ms), high memory            |

---

## Scope

### 1. Baseline measurement

- Add timing/logging around `generate_pdf()` in `pdf_generator.py` and `export_pdf()` in `emission_export.py`.
- Measure typical DA (e.g. 5–20 line items) and MRV report generation time.
- Capture metrics: wall-clock time, memory before/after.

### 2. Quick wins (WeasyPrint stay)

- **Template optimization:** Replace `display: grid` with flexbox or tables in `DA_TEMPLATE` and emission report HTML. Benchmark before/after.
- **Font/config:** Ensure minimal font loading; avoid unnecessary `@font-face` or external resources.
- **Worker tuning:** Confirm PDF generation runs in a dedicated worker process (not blocking API); consider process pool if single-threaded.

### 3. Alternative library evaluation

- **ReportLab:** Implement a DA PDF renderer using ReportLab’s `Table`, `Paragraph`, `SimpleDocTemplate`. Compare quality and speed vs WeasyPrint.
- **FPDF2:** Prototype same DA layout with `FPDF`; measure speed.
- Document findings: speed gain, visual parity, migration effort.

### 4. Recommendation and implementation

- Choose strategy: (a) optimize WeasyPrint, (b) migrate to ReportLab/FPDF2, or (c) hybrid (ReportLab for DA, keep WeasyPrint for MRV if different needs).
- Implement chosen approach; ensure `pdf_generator.generate_pdf` and `emission_export.export_pdf` maintain same function signatures.
- Update dependencies (`pyproject.toml`); add/remove as needed.

---

## Acceptance criteria

- [x] Baseline metrics documented (current WeasyPrint time for typical DA and MRV).
- [x] At least one optimization applied (template change or library migration).
- [x] PDF generation time improved by measurable amount (target: &lt; 200 ms for single DA PDF).
- [x] Visual output remains acceptable (no regressions in layout or branding).
- [x] Tests updated if PDF generation logic changes.
- [x] Findings and chosen approach documented (in task or `docs/`).

---

## Related code

- `backend/app/services/pdf_generator.py` — `generate_pdf`, `DA_TEMPLATE`, `render_da_html`
- `backend/app/services/emission_export.py` — `export_pdf`, `_render_emission_report_html`
- `backend/app/services/da_worker.py` — calls `generate_pdf`
- `backend/pyproject.toml` — `weasyprint>=62.0`

---

## References

- [Speedata typesetting benchmark (WeasyPrint vs Typst, pdflatex, etc.)](https://news.speedata.de/2026/02/10/typesetting-benchmark/)
- [WeasyPrint Issue #2336 — Grid layout performance](https://github.com/Kozea/WeasyPrint/issues/2336)
- [Python PDF libraries compared (2025)](https://templated.io/blog/generate-pdfs-in-python-with-libraries/)
- [Task 3.12 — Fix DA PDF generation: no response](task-12-fix-da-pdf-generation-no-response.md)
- [Task 3.7 — PDF generation worker](task-07-pdf-generation-worker.md)
