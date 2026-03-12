"""Tests for DA formula engine (line items and totals from parsed email data)."""

import pytest

from app.services.formula_engine import compute_line_items


def test_parsed_line_items_only():
    """Compute line items from parsed email data when no tariff config."""
    formula_config = {"items": [], "tax_rate": 0}
    vessel_data = {"name": "MV Atlantic Star", "imo": "9123456", "grt": 0, "nrt": 0}
    port_call_data = {"eta": "2025-03-15T06:00:00", "etd": "2025-03-16T18:00:00"}
    parsed_line_items = [
        {"description": "Pilotage", "amount": 1850.0, "currency": "USD", "quantity": 1.0},
        {
            "description": "Port dues (per GRT)",
            "amount": 10625.0,
            "currency": "USD",
            "quantity": 12500.0,
            "unit_price": 0.85,
        },
        {
            "description": "Berth hire",
            "amount": 2312.5,
            "currency": "USD",
            "quantity": 18.5,
            "unit_price": 125.0,
        },
        {"description": "Mooring/unmooring", "amount": 420.0, "currency": "USD"},
        {"description": "Agency fee", "amount": 750.0, "currency": "USD"},
    ]

    items, totals = compute_line_items(
        formula_config, vessel_data, port_call_data, parsed_line_items
    )

    assert len(items) == 5
    assert items[0]["description"] == "Pilotage"
    assert items[0]["amount"] == pytest.approx(1850.0)
    assert items[4]["description"] == "Agency fee"
    assert items[4]["amount"] == pytest.approx(750.0)

    assert totals["subtotal"] == pytest.approx(15957.5)
    assert totals["tax"] == pytest.approx(0.0)
    assert totals["total"] == pytest.approx(15957.5)
    assert totals["currency"] == "USD"


def test_parsed_line_items_with_tariff_config():
    """Parsed items are appended to tariff-computed items."""
    formula_config = {
        "items": [{"description": "Base fee", "type": "fixed", "rate": 100.0, "currency": "USD"}],
        "tax_rate": 0,
    }
    vessel_data = {"grt": 0, "nrt": 0}
    port_call_data = {}
    parsed_line_items = [
        {"description": "Pilotage", "amount": 500.0, "currency": "USD"},
    ]

    items, totals = compute_line_items(
        formula_config, vessel_data, port_call_data, parsed_line_items
    )

    assert len(items) == 2
    assert items[0]["description"] == "Base fee"
    assert items[0]["amount"] == pytest.approx(100.0)
    assert items[1]["description"] == "Pilotage"
    assert items[1]["amount"] == pytest.approx(500.0)
    assert totals["total"] == pytest.approx(600.0)


def test_parsed_line_items_minimal_fields():
    """Parsed item with only description and amount uses defaults."""
    formula_config = {"items": [], "tax_rate": 0}
    vessel_data = {}
    port_call_data = {}
    parsed_line_items = [
        {"description": "Agency fee", "amount": 750.0},
    ]

    items, totals = compute_line_items(
        formula_config, vessel_data, port_call_data, parsed_line_items
    )

    assert len(items) == 1
    assert items[0]["description"] == "Agency fee"
    assert items[0]["amount"] == pytest.approx(750.0)
    assert items[0]["currency"] == "USD"
    assert items[0]["quantity"] == 1
    assert totals["total"] == pytest.approx(750.0)


def test_empty_parsed_line_items():
    """No parsed items with empty tariff yields empty items."""
    formula_config = {"items": [], "tax_rate": 0}
    items, totals = compute_line_items(formula_config, {}, {}, parsed_line_items=None)
    assert len(items) == 0
    assert totals["subtotal"] == pytest.approx(0.0)
    assert totals["total"] == pytest.approx(0.0)
