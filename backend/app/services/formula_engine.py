"""DA formula engine — computes line items and totals from port call + tariff.

Tariff formula_config structure:
{
    "items": [
        {
            "description": "Pilotage",
            "type": "per_call" | "per_ton" | "per_hour" | "fixed",
            "rate": 150.0,
            "currency": "USD"
        },
        ...
    ],
    "tax_rate": 0.0
}

Port call inputs used: vessel GRT/NRT (from vessel), duration hours, etc.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("shipflow.formula_engine")


def compute_line_items(
    formula_config: dict[str, Any],
    vessel_data: dict[str, Any],
    port_call_data: dict[str, Any],
    parsed_line_items: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return (line_items, totals) computed from tariff config and inputs.

    Each line item: {description, quantity, unit_price, amount, currency}.
    Totals: {subtotal, tax, total, currency}.
    """
    items: list[dict[str, Any]] = []
    config_items = formula_config.get("items", [])
    tax_rate = formula_config.get("tax_rate", 0.0)
    default_currency = formula_config.get("currency", "USD")

    grt = vessel_data.get("grt", 0) or 0
    nrt = vessel_data.get("nrt", 0) or 0
    tonnage = grt if grt > 0 else nrt

    eta = port_call_data.get("eta")
    etd = port_call_data.get("etd")
    duration_hours = 24.0
    if eta and etd:
        try:
            from datetime import datetime

            t_eta = datetime.fromisoformat(str(eta)) if isinstance(eta, str) else eta
            t_etd = datetime.fromisoformat(str(etd)) if isinstance(etd, str) else etd
            duration_hours = max((t_etd - t_eta).total_seconds() / 3600, 1.0)
        except (ValueError, TypeError):
            pass

    for cfg_item in config_items:
        desc = cfg_item.get("description", "Charge")
        rate = float(cfg_item.get("rate", 0))
        charge_type = cfg_item.get("type", "fixed")
        currency = cfg_item.get("currency", default_currency)

        if charge_type == "per_call":
            qty = 1.0
            amount = rate
        elif charge_type == "per_ton":
            qty = float(tonnage)
            amount = rate * qty
        elif charge_type == "per_hour":
            qty = round(duration_hours, 2)
            amount = rate * qty
        else:
            qty = 1.0
            amount = rate

        items.append({
            "description": desc,
            "quantity": qty,
            "unit_price": rate,
            "amount": round(amount, 2),
            "currency": currency,
        })

    if parsed_line_items:
        for pli in parsed_line_items:
            items.append({
                "description": pli.get("description", "Parsed item"),
                "quantity": pli.get("quantity", 1) or 1,
                "unit_price": pli.get("unit_price", pli.get("amount", 0)) or 0,
                "amount": round(float(pli.get("amount", 0)), 2),
                "currency": pli.get("currency", default_currency),
            })

    subtotal = round(sum(item["amount"] for item in items), 2)
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    totals = {
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "currency": default_currency,
    }

    return items, totals
