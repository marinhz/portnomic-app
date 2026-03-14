"""Tests for PDF generation (DA and emission report)."""

import asyncio

import pytest

from app.services.pdf_generator import generate_pdf, render_da_html


def test_render_da_html_basic():
    """render_da_html produces valid HTML with DA fields."""
    da_data = {
        "id": "abc-123",
        "type": "proforma",
        "version": 2,
        "status": "approved",
        "currency": "USD",
        "line_items": [
            {"description": "Pilotage", "quantity": 1, "unit_price": 1500.0, "amount": 1500.0},
        ],
        "totals": {"subtotal": 1500.0, "tax": 0.0, "total": 1500.0},
    }
    html = render_da_html(da_data)
    assert "ShipFlow" in html
    assert "abc-123" in html or "abc-12" in html
    assert "Proforma" in html
    assert "Pilotage" in html
    assert "1,500.00" in html
    assert "USD" in html
    # Template uses flexbox for meta-grid (WeasyPrint perf optimization)
    assert "display: flex" in html
    assert "grid-template-columns" not in html


def test_generate_pdf_returns_bytes():
    """generate_pdf returns bytes (PDF when WeasyPrint available, else HTML)."""
    da_data = {
        "id": "test-id",
        "type": "final",
        "version": 1,
        "status": "draft",
        "currency": "EUR",
        "line_items": [
            {"description": "Agency fee", "quantity": 1, "unit_price": 500.0, "amount": 500.0},
        ],
        "totals": {"subtotal": 500.0, "tax": 50.0, "total": 550.0},
    }
    result = asyncio.run(generate_pdf(da_data))
    assert isinstance(result, bytes)
    assert len(result) > 0
    # ReportLab (primary) or WeasyPrint produce PDF; fallback is HTML when neither available
    assert (
        result.startswith(b"%PDF")
        or b"<!DOCTYPE" in result
        or b"html" in result.lower()
    ), "Expected PDF or HTML fallback"


def test_export_pdf_returns_tuple():
    """export_pdf returns (bytes, media_type) for MRV report."""
    try:
        from app.services.emission_export import export_pdf
    except ImportError:
        pytest.skip("emission_export dependencies not installed")

    mrv_data = {
        "report_id": "rpt-001",
        "reporting_period": {"start_date": "2025-01-01", "end_date": "2025-01-31"},
        "vessel": {"name": "MV Test", "imo_number": "1234567"},
        "co2_emissions": {
            "total_mt": 100.5,
            "per_fuel_breakdown": [
                {
                    "fuel_type": "MDO",
                    "consumption_mt": 25.0,
                    "emission_factor": 3.2,
                    "co2_mt": 80.0,
                }
            ],
        },
        "fuel_consumption_by_type": [
            {"fuel_type": "MDO", "consumption_mt": 25.0, "operational_status": "at_sea"}
        ],
        "distance_nm": 150.0,
        "time_at_berth_eu_mt": 5.0,
        "status": "draft",
        "source_email_id": "N/A",
    }
    content, media_type = export_pdf(mrv_data)
    assert isinstance(content, bytes)
    assert len(content) > 0
    assert media_type in ("application/pdf", "text/html")
    if media_type == "application/pdf":
        assert content.startswith(b"%PDF")
