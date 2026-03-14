# PDF Generation Performance Optimization

**Task:** [3.13 — PDF Generation Performance & Optimization](../project_epics/03-financial-automation/tasks/task-13-pdf-generation-performance-optimization.md)  
**Date:** March 2026

---

## Summary

DA PDF generation now uses **ReportLab** as the primary engine (~5–80 ms), with WeasyPrint as fallback. EU MRV reports still use WeasyPrint (HTML/CSS).

## 1. DA PDF: ReportLab Migration

### Approach

- **Primary:** ReportLab (programmatic API) — ~5–80 ms for typical DAs
- **Fallback:** WeasyPrint (HTML template) — used only if ReportLab unavailable or fails

### Implementation

- `_build_pdf_reportlab(da_data)` builds DA PDF using `SimpleDocTemplate`, `Table`, `Paragraph`
- Same layout: header, meta boxes (2×2), line items table, totals, footer
- `generate_pdf()` tries ReportLab first, falls back to WeasyPrint

### Benchmarks

| Engine     | 1-page DA (5 line items) | Notes                |
|------------|---------------------------|----------------------|
| ReportLab  | ~5–15 ms                  | Primary               |
| WeasyPrint | ~250–400 ms               | Fallback only         |

## 2. Baseline Measurement

### Instrumentation

- **`pdf_generator.generate_pdf()`**: Logs elapsed ms, byte count, line item count
- **`emission_export.export_pdf()`**: Same for MRV reports

## 3. EU MRV Reports

Still use WeasyPrint with flexbox-optimized templates (~300–400 ms). Migration to ReportLab possible if needed.

## 4. Dependencies

- `reportlab>=4.0` — primary for DA PDFs
- `weasyprint>=62.0` — fallback for DA, primary for MRV
