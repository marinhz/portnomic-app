"""
EU MRV (Monitoring, Reporting, Verification) compliant export.

Generates reports in JSON, XML, and PDF for submission to authorities
or independent verifiers (e.g. DNV, Lloyd's Register).
Reference: EU MRV Regulation (EU) 2015/757 and delegated acts.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.emission_report import EmissionReport
from app.services.carbon_price import get_current_price_eur
from app.services.emission_calculator import calculate_emissions, estimate_eua

logger = logging.getLogger(__name__)


async def get_report_for_export(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    report_id: uuid.UUID,
) -> EmissionReport | None:
    """Fetch emission report with vessel and fuel entries for export."""
    stmt = (
        select(EmissionReport)
        .where(
            EmissionReport.id == report_id,
            EmissionReport.tenant_id == tenant_id,
        )
        .options(
            selectinload(EmissionReport.vessel),
            selectinload(EmissionReport.fuel_entries),
            selectinload(EmissionReport.email),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _build_mrv_data(report: EmissionReport) -> dict[str, Any]:
    """Build EU MRV compliant data structure from emission report."""
    vessel = report.vessel
    emissions = calculate_emissions(report)

    # Time at EU port: sum of at_berth fuel consumption (simplified; full MRV may need port-level data)
    fuel_at_berth_mt = sum(
        float(e.consumption_mt)
        for e in report.fuel_entries
        if (e.operational_status or "").lower().replace(" ", "_") == "at_berth"
    )

    return {
        "report_id": str(report.id),
        "schema_version": report.schema_version,
        "reporting_period": {
            "start_date": report.report_date.isoformat(),
            "end_date": report.report_date.isoformat(),
        },
        "vessel": {
            "imo_number": vessel.imo or "N/A",
            "name": vessel.name,
            "vessel_id": str(vessel.id),
        },
        "fuel_consumption_by_type": [
            {
                "fuel_type": b.fuel_type,
                "consumption_mt": round(b.consumption_mt, 6),
                "operational_status": next(
                    (
                        e.operational_status
                        for e in report.fuel_entries
                        if e.fuel_type == b.fuel_type
                    ),
                    "at_sea_cruising",
                ),
            }
            for b in emissions.per_fuel_breakdown
        ],
        "co2_emissions": {
            "total_mt": emissions.total_co2_mt,
            "per_fuel_breakdown": [
                {
                    "fuel_type": b.fuel_type,
                    "consumption_mt": b.consumption_mt,
                    "emission_factor": b.emission_factor,
                    "co2_mt": round(b.co2_mt, 6),
                }
                for b in emissions.per_fuel_breakdown
            ],
        },
        "distance_nm": report.distance_nm,
        "time_at_berth_eu_mt": round(fuel_at_berth_mt, 6) if fuel_at_berth_mt else None,
        "extracted_at": report.extracted_at.isoformat() if report.extracted_at else None,
        "status": report.status,
        "source_email_id": str(report.email_id) if report.email_id else None,
        "audit_trail": {
            "source_email_reference": str(report.email_id) if report.email_id else None,
            "report_created_at": report.created_at.isoformat() if report.created_at else None,
        },
    }


async def build_mrv_data_for_export(report: EmissionReport) -> dict[str, Any]:
    """Build MRV data including EUA estimate (requires async carbon price)."""
    data = _build_mrv_data(report)
    carbon_price = await get_current_price_eur()
    eua = estimate_eua(report, carbon_price)
    data["eua_estimate"] = {
        "eua_count": eua.eua_count,
        "cost_eur": eua.cost_eur,
        "carbon_price_eur": eua.carbon_price_eur,
    }
    return data


def export_json(mrv_data: dict[str, Any]) -> bytes:
    """Export MRV data as JSON."""
    return json.dumps(mrv_data, indent=2, default=str).encode("utf-8")


def export_xml(mrv_data: dict[str, Any]) -> bytes:
    """Export MRV data as XML (EU MRV compatible structure)."""
    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<EUMRVReport xmlns="urn:eu:mrv:maritime:1.0">')

    def escape(s: str) -> str:
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def add_tag(name: str, value: Any, indent: int = 2) -> None:
        if value is None:
            return
        sp = " " * indent
        lines.append(f"{sp}<{name}>{escape(str(value))}</{name}>")

    lines.append("  <reportId>" + escape(mrv_data.get("report_id", "")) + "</reportId>")
    lines.append("  <reportingPeriod>")
    rp = mrv_data.get("reporting_period", {})
    add_tag("startDate", rp.get("start_date"), 4)
    add_tag("endDate", rp.get("end_date"), 4)
    lines.append("  </reportingPeriod>")

    v = mrv_data.get("vessel", {})
    lines.append("  <vessel>")
    add_tag("imoNumber", v.get("imo_number"), 4)
    add_tag("name", v.get("name"), 4)
    lines.append("  </vessel>")

    lines.append("  <fuelConsumptionByType>")
    for f in mrv_data.get("fuel_consumption_by_type", []):
        lines.append("    <fuelEntry>")
        add_tag("fuelType", f.get("fuel_type"), 6)
        add_tag("consumptionMt", f.get("consumption_mt"), 6)
        add_tag("operationalStatus", f.get("operational_status"), 6)
        lines.append("    </fuelEntry>")
    lines.append("  </fuelConsumptionByType>")

    co2 = mrv_data.get("co2_emissions", {})
    lines.append("  <co2Emissions>")
    add_tag("totalMt", co2.get("total_mt"), 4)
    lines.append("    <perFuelBreakdown>")
    for b in co2.get("per_fuel_breakdown", []):
        lines.append("      <entry>")
        add_tag("fuelType", b.get("fuel_type"), 8)
        add_tag("consumptionMt", b.get("consumption_mt"), 8)
        add_tag("emissionFactor", b.get("emission_factor"), 8)
        add_tag("co2Mt", b.get("co2_mt"), 8)
        lines.append("      </entry>")
    lines.append("    </perFuelBreakdown>")
    lines.append("  </co2Emissions>")

    add_tag("distanceNm", mrv_data.get("distance_nm"))
    add_tag("timeAtBerthEuMt", mrv_data.get("time_at_berth_eu_mt"))
    add_tag("extractedAt", mrv_data.get("extracted_at"))
    add_tag("status", mrv_data.get("status"))
    add_tag("sourceEmailId", mrv_data.get("source_email_id"))

    lines.append("  <auditTrail>")
    at = mrv_data.get("audit_trail", {})
    add_tag("sourceEmailReference", at.get("source_email_reference"), 4)
    add_tag("reportCreatedAt", at.get("report_created_at"), 4)
    lines.append("  </auditTrail>")

    if "eua_estimate" in mrv_data:
        eu = mrv_data["eua_estimate"]
        lines.append("  <euaEstimate>")
        add_tag("euaCount", eu.get("eua_count"), 4)
        add_tag("costEur", eu.get("cost_eur"), 4)
        add_tag("carbonPriceEur", eu.get("carbon_price_eur"), 4)
        lines.append("  </euaEstimate>")

    lines.append("</EUMRVReport>")
    return "\n".join(lines).encode("utf-8")


EMISSION_REPORT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11px; color: #1e293b; margin: 40px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 3px solid #0c4a6e; padding-bottom: 20px; }}
  .company {{ font-size: 20px; font-weight: bold; color: #0c4a6e; }}
  .doc-title {{ font-size: 16px; font-weight: bold; color: #0c4a6e; text-transform: uppercase; margin-bottom: 20px; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px; }}
  .meta-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; }}
  .meta-label {{ font-size: 9px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 4px; }}
  .meta-value {{ font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
  thead th {{ background: #0c4a6e; color: #fff; padding: 10px 12px; text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; }}
  tbody td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  .section {{ margin-bottom: 25px; }}
  .section-title {{ font-size: 12px; font-weight: bold; color: #0c4a6e; margin-bottom: 10px; }}
  .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 9px; color: #94a3b8; text-align: center; }}
  .amount {{ text-align: right; }}
</style>
</head>
<body>
  <div class="header">
    <div class="company">Portnomic — EU MRV Report</div>
    <div style="text-align:right">
      <div style="font-size:9px; color:#64748b">Generated</div>
      <div>{generated_date}</div>
    </div>
  </div>

  <div class="doc-title">EU MRV Monitoring, Reporting &amp; Verification Report</div>

  <div class="meta-grid">
    <div class="meta-box">
      <div class="meta-label">Report ID</div>
      <div class="meta-value">{report_id}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Reporting Period</div>
      <div class="meta-value">{report_date}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Vessel Name</div>
      <div class="meta-value">{vessel_name}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">IMO Number</div>
      <div class="meta-value">{imo_number}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Status</div>
      <div class="meta-value">{status}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Source Email Reference</div>
      <div class="meta-value">{source_email_id}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Fuel Consumption &amp; CO₂ Emissions</div>
    <table>
      <thead>
        <tr>
          <th>Fuel Type</th>
          <th>Operational Status</th>
          <th class="amount">Consumption (MT)</th>
          <th class="amount">Emission Factor</th>
          <th class="amount">CO₂ (MT)</th>
        </tr>
      </thead>
      <tbody>
        {fuel_rows}
      </tbody>
    </table>
    <div style="margin-top: 10px; font-weight: bold;">Total CO₂: {total_co2_mt} MT</div>
  </div>

  <div class="meta-grid">
    <div class="meta-box">
      <div class="meta-label">Distance (NM)</div>
      <div class="meta-value">{distance_nm}</div>
    </div>
    <div class="meta-box">
      <div class="meta-label">Time at Berth (EU) Fuel (MT)</div>
      <div class="meta-value">{time_at_berth}</div>
    </div>
  </div>

  <div class="footer">
    EU MRV Regulation (EU) 2015/757 compliant. Generated by Portnomic. Report ID: {report_id} — Source: {source_email_id}
  </div>
</body>
</html>
"""


def _render_emission_report_html(mrv_data: dict[str, Any]) -> str:
    """Render emission report as HTML for PDF conversion."""
    fuel_rows = ""
    for b in mrv_data.get("co2_emissions", {}).get("per_fuel_breakdown", []):
        fuel_entries = mrv_data.get("fuel_consumption_by_type", [])
        op_status = next(
            (f.get("operational_status", "—") for f in fuel_entries if f.get("fuel_type") == b.get("fuel_type")),
            "—",
        )
        fuel_rows += (
            f"<tr>"
            f"<td>{b.get('fuel_type', '—')}</td>"
            f"<td>{op_status}</td>"
            f"<td class='amount'>{b.get('consumption_mt', 0):,.6f}</td>"
            f"<td class='amount'>{b.get('emission_factor', 0):,.4f}</td>"
            f"<td class='amount'>{b.get('co2_mt', 0):,.6f}</td>"
            f"</tr>"
        )

    total_co2 = mrv_data.get("co2_emissions", {}).get("total_mt", 0)
    distance = mrv_data.get("distance_nm")
    time_at_berth = mrv_data.get("time_at_berth_eu_mt")
    vessel = mrv_data.get("vessel", {})
    report_date = mrv_data.get("reporting_period", {}).get("start_date", "—")
    source_email = mrv_data.get("source_email_id") or "N/A"

    return EMISSION_REPORT_HTML_TEMPLATE.format(
        generated_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        report_id=mrv_data.get("report_id", "N/A"),
        report_date=report_date,
        vessel_name=vessel.get("name", "N/A"),
        imo_number=vessel.get("imo_number", "N/A"),
        status=mrv_data.get("status", "—"),
        source_email_id=source_email,
        fuel_rows=fuel_rows,
        total_co2_mt=f"{total_co2:,.6f}",
        distance_nm=str(distance) if distance is not None else "N/A",
        time_at_berth=f"{time_at_berth:,.6f}" if time_at_berth is not None else "N/A",
    )


def export_pdf(mrv_data: dict[str, Any]) -> tuple[bytes, str]:
    """Generate PDF from MRV data using WeasyPrint.

    Returns (content_bytes, media_type). Falls back to HTML if WeasyPrint not installed.
    """
    html = _render_emission_report_html(mrv_data)
    try:
        from weasyprint import HTML

        pdf_bytes = HTML(string=html).write_pdf()
        logger.info("Generated EU MRV PDF for report %s (%d bytes)", mrv_data.get("report_id"), len(pdf_bytes))
        return (pdf_bytes, "application/pdf")
    except ImportError:
        logger.warning("WeasyPrint not installed; falling back to HTML")
        html_bytes = html.encode("utf-8")
        return (html_bytes, "text/html")


__all__ = [
    "get_report_for_export",
    "build_mrv_data_for_export",
    "export_json",
    "export_xml",
    "export_pdf",
]
