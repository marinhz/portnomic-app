"""PDF generation for Disbursement Accounts.

Uses ReportLab (fast) as primary; falls back to WeasyPrint if ReportLab unavailable.
"""

import io
import logging
import time
from datetime import datetime

logger = logging.getLogger("shipflow.pdf_generator")

# Brand colors (from original template)
_PRIMARY = "#0c4a6e"
_LIGHT_BG = "#f8fafc"
_BORDER = "#e2e8f0"
_MUTED = "#64748b"
_TEXT = "#1e293b"
_FOOTER = "#94a3b8"


def _build_pdf_reportlab(da_data: dict) -> bytes:
    """Generate DA PDF using ReportLab (fast, programmatic API)."""
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    primary = HexColor(_PRIMARY)
    light_bg = HexColor(_LIGHT_BG)
    border = HexColor(_BORDER)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    elements = []

    generated_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    da_type = da_data.get("type", "Proforma").title()
    da_id = str(da_data.get("id", ""))
    da_id_short = da_id[:8] if da_id else "N/A"
    version = da_data.get("version", 1)
    status = da_data.get("status", "draft").replace("_", " ").title()
    currency = da_data.get("currency", "USD")
    totals = da_data.get("totals", {})

    # Header: ShipFlow | Generated date (fits 7")
    header_table = Table(
        [[
            Paragraph('<b><font color="#0c4a6e" size="18">ShipFlow</font></b>', styles["Normal"]),
            Paragraph(f'<font size="9" color="#64748b">Generated</font><br/>{generated_date}', styles["Normal"]),
        ]],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 3, primary),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.2 * inch))

    # Title
    title = Paragraph(
        f'<b><font color="{_PRIMARY}" size="14">{da_type} Disbursement Account</font></b>',
        styles["Normal"],
    )
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    # Meta boxes (2x2 grid)
    meta_rows = [
        [Paragraph('<font size="8" color="#64748b">DA REFERENCE</font>', styles["Normal"]), Paragraph(f'<b>{da_id_short}</b>', styles["Normal"]),
        Paragraph('<font size="8" color="#64748b">VERSION</font>', styles["Normal"]), Paragraph(f'<b>v{version}</b>', styles["Normal"])],
        [Paragraph('<font size="8" color="#64748b">STATUS</font>', styles["Normal"]), Paragraph(f'<b>{status}</b>', styles["Normal"]),
        Paragraph('<font size="8" color="#64748b">CURRENCY</font>', styles["Normal"]), Paragraph(f'<b>{currency}</b>', styles["Normal"])],
    ]
    # Meta: 4 cols fitting 7" (1.75" each)
    meta_table = Table(meta_rows, colWidths=[1.75 * inch] * 4)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_bg),
        ("BOX", (0, 0), (-1, -1), 1, border),
        ("INNERGRID", (0, 0), (-1, -1), 1, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.25 * inch))

    # Line items table (fits 7"); use Paragraph for description to wrap long text
    line_items = da_data.get("line_items", [])
    table_data = [
        ["Description", "Qty", "Unit Price", "Amount"],
    ]
    for item in line_items:
        desc = (item.get("description", "") or "").replace("&", "&amp;").replace("<", "&lt;")
        table_data.append([
            Paragraph(desc, styles["Normal"]) if desc else "",
            str(item.get("quantity", 1)),
            f"{item.get('unit_price', 0):,.2f}",
            f"{item.get('amount', 0):,.2f}",
        ])

    col_widths = [3.2 * inch, 0.55 * inch, 1.5 * inch, 1.5 * inch]  # total ~6.75"
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), primary),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.15 * inch))

    # Totals
    subtotal = f"{totals.get('subtotal', 0):,.2f}"
    tax = f"{totals.get('tax', 0):,.2f}"
    total = f"{totals.get('total', 0):,.2f}"
    totals_data = [
        ["", "Subtotal:", f"{currency} {subtotal}"],
        ["", "Tax:", f"{currency} {tax}"],
        ["", "Total:", f"{currency} {total}"],
    ]
    totals_table = Table(totals_data, colWidths=[4 * inch, 1.2 * inch, 1.5 * inch])  # ~6.7"
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (1, 2), (2, 2), 2, primary),
        ("FONTNAME", (1, 2), (2, 2), "Helvetica-Bold"),
        ("FONTSIZE", (1, 2), (2, 2), 12),
        ("TEXTCOLOR", (1, 2), (2, 2), primary),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 0.4 * inch))

    # Footer
    footer = Paragraph(
        f'<font size="8" color="{_FOOTER}">This document was generated by ShipFlow AI &mdash; {generated_date}</font>',
        ParagraphStyle(name="Footer", parent=styles["Normal"], alignment=1, spaceAfter=0),
    )
    elements.append(footer)

    doc.build(elements)
    return buffer.getvalue()


# WeasyPrint fallback (HTML template)
DA_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11px; color: #1e293b; margin: 40px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 3px solid #0c4a6e; padding-bottom: 20px; }}
  .company {{ font-size: 20px; font-weight: bold; color: #0c4a6e; }}
  .doc-title {{ font-size: 16px; font-weight: bold; color: #0c4a6e; text-transform: uppercase; margin-bottom: 20px; }}
  .meta-grid {{ display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 25px; }}
  .meta-box {{ flex: 1 1 calc(50% - 8px); min-width: 0; box-sizing: border-box; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; }}
  .meta-label {{ font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 4px; }}
  .meta-value {{ font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  thead th {{ background: #0c4a6e; color: #fff; padding: 10px 12px; text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; }}
  tbody td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  .totals {{ margin-top: 10px; text-align: right; }}
  .totals .row {{ display: flex; justify-content: flex-end; gap: 40px; padding: 6px 12px; }}
  .totals .total {{ font-size: 14px; font-weight: bold; color: #0c4a6e; border-top: 2px solid #0c4a6e; padding-top: 8px; }}
  .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 9px; color: #94a3b8; text-align: center; }}
  .amount {{ text-align: right; }}
  .qty {{ text-align: center; }}
</style>
</head>
<body>
  <div class="header">
    <div class="company">ShipFlow</div>
    <div style="text-align:right">
      <div style="font-size:9px; color:#64748b">Generated</div>
      <div>{generated_date}</div>
    </div>
  </div>

  <div class="doc-title">{da_type} Disbursement Account</div>

  <div class="meta-grid">
    <div class="meta-box">
      <div class="meta-label">DA Reference</div>
      <div class="meta-value">{da_id_short}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Version</div>
      <div class="meta-value">v{version}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Status</div>
      <div class="meta-value">{status}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Currency</div>
      <div class="meta-value">{currency}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width:50%">Description</th>
        <th class="qty">Qty</th>
        <th class="amount">Unit Price</th>
        <th class="amount">Amount</th>
      </tr>
    </thead>
    <tbody>
      {line_items_rows}
    </tbody>
  </table>

  <div class="totals">
    <div class="row"><span>Subtotal:</span><span>{currency} {subtotal}</span></div>
    <div class="row"><span>Tax:</span><span>{currency} {tax}</span></div>
    <div class="row total"><span>Total:</span><span>{currency} {total}</span></div>
  </div>

  <div class="footer">
    This document was generated by ShipFlow AI &mdash; {generated_date}
  </div>
</body>
</html>
"""


def render_da_html(da_data: dict) -> str:
    """Render DA as HTML (for WeasyPrint fallback)."""
    line_items = da_data.get("line_items", [])
    totals = da_data.get("totals", {})
    currency = da_data.get("currency", "USD")

    rows = ""
    for item in line_items:
        rows += (
            f"<tr>"
            f"<td>{item.get('description', '')}</td>"
            f'<td class="qty">{item.get("quantity", 1)}</td>'
            f'<td class="amount">{item.get("unit_price", 0):,.2f}</td>'
            f'<td class="amount">{item.get("amount", 0):,.2f}</td>'
            f"</tr>"
        )

    da_id = str(da_data.get("id", ""))
    return DA_TEMPLATE.format(
        generated_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        da_type=da_data.get("type", "Proforma").title(),
        da_id_short=da_id[:8] if da_id else "N/A",
        version=da_data.get("version", 1),
        status=da_data.get("status", "draft").replace("_", " ").title(),
        currency=currency,
        line_items_rows=rows,
        subtotal=f"{totals.get('subtotal', 0):,.2f}",
        tax=f"{totals.get('tax', 0):,.2f}",
        total=f"{totals.get('total', 0):,.2f}",
    )


async def generate_pdf(da_data: dict) -> bytes:
    """Generate PDF bytes from DA data dict.

    Uses ReportLab (fast) when available; falls back to WeasyPrint (HTML).
    """
    t0 = time.perf_counter()
    pdf_bytes: bytes

    try:
        pdf_bytes = _build_pdf_reportlab(da_data)
        if not pdf_bytes.startswith(b"%PDF"):
            raise RuntimeError("ReportLab did not produce valid PDF")
    except (ImportError, RuntimeError) as e:
        logger.debug("ReportLab unavailable or failed (%s), using WeasyPrint fallback", e)
        html = render_da_html(da_data)
        try:
            from weasyprint import HTML

            pdf_bytes = HTML(string=html).write_pdf()
        except ImportError:
            logger.warning("WeasyPrint not installed; falling back to HTML-as-PDF placeholder")
            pdf_bytes = html.encode("utf-8")

    elapsed_ms = (time.perf_counter() - t0) * 1000
    line_count = len(da_data.get("line_items", []))
    logger.info(
        "Generated PDF for DA %s (%d bytes, %d line items) in %.1f ms",
        da_data.get("id", "?"),
        len(pdf_bytes),
        line_count,
        elapsed_ms,
    )
    return pdf_bytes
