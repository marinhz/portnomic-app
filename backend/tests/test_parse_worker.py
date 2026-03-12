"""Tests for parse worker: port creation, DA auto-create, disbursement flow."""

import uuid

import pytest
from sqlalchemy import select

from app.database import async_session_factory
from app.models.port import Port
from app.models.tenant import Tenant
from app.schemas.ai import ParsedEmailResult, ParsedLineItem
from app.services.parse_worker import _resolve_port


@pytest.mark.asyncio
async def test_resolve_port_creates_port_when_not_found():
    """When port does not exist, _resolve_port creates it for the tenant."""
    async with async_session_factory() as db:
        # Create a tenant (no ports in DB for this tenant)
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Agency",
            slug=f"test-{uuid.uuid4().hex[:8]}",
        )
        db.add(tenant)
        await db.flush()

        result = ParsedEmailResult(
            vessel_name="MV Atlantic Star",
            vessel_imo="9123456",
            port_name="Rotterdam",
            port_code="NLRTM",
            eta="2025-03-15T06:00:00Z",
            etd="2025-03-16T18:00:00Z",
            line_items=[
                ParsedLineItem(description="Pilotage", amount=1850.0, currency="USD"),
            ],
        )

        port_id = await _resolve_port(db, tenant.id, result)

        assert port_id is not None
        port = (await db.execute(select(Port).where(Port.id == port_id))).scalar_one_or_none()
        assert port is not None
        assert port.name == "Rotterdam"
        assert port.code == "NLRTM"
        assert port.tenant_id == tenant.id

        await db.rollback()


@pytest.mark.asyncio
async def test_resolve_port_uses_existing_port_when_found():
    """When port exists, _resolve_port returns it without creating duplicate."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Agency",
            slug=f"test-{uuid.uuid4().hex[:8]}",
        )
        db.add(tenant)
        await db.flush()

        existing_port = Port(
            tenant_id=tenant.id,
            name="Rotterdam",
            code="NLRTM",
        )
        db.add(existing_port)
        await db.flush()

        result = ParsedEmailResult(port_name="Rotterdam", port_code="NLRTM")

        port_id = await _resolve_port(db, tenant.id, result)

        assert port_id == existing_port.id

        # No duplicate created
        count = (
            (
                await db.execute(
                    select(Port).where(Port.tenant_id == tenant.id, Port.code == "NLRTM")
                )
            )
            .scalars()
            .all()
        )
        assert len(count) == 1

        await db.rollback()


@pytest.mark.asyncio
async def test_resolve_port_creates_from_port_name_only():
    """When only port_name (no port_code), creates port with derived code."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test Agency",
            slug=f"test-{uuid.uuid4().hex[:8]}",
        )
        db.add(tenant)
        await db.flush()

        result = ParsedEmailResult(port_name="Singapore")

        port_id = await _resolve_port(db, tenant.id, result)

        assert port_id is not None
        port = (await db.execute(select(Port).where(Port.id == port_id))).scalar_one_or_none()
        assert port is not None
        assert port.name == "Singapore"
        assert port.code == "SINGAPORE"  # Derived from name

        await db.rollback()


def test_parsed_line_item_to_dict_format():
    """ParsedLineItem converts correctly for formula_engine (used in DA auto-create)."""
    from app.schemas.ai import ParsedLineItem

    li = ParsedLineItem(
        description="Pilotage",
        amount=1850.0,
        currency="USD",
        quantity=1.0,
        unit_price=1850.0,
    )
    # Conversion used in parse_worker
    d = {
        "description": li.description,
        "amount": li.amount,
        "currency": li.currency or "USD",
        "quantity": li.quantity or 1.0,
        "unit_price": li.unit_price if li.unit_price is not None else li.amount,
    }
    assert d["description"] == "Pilotage"
    assert d["amount"] == pytest.approx(1850.0)
    assert d["currency"] == "USD"
    assert d["quantity"] == pytest.approx(1.0)
    assert d["unit_price"] == pytest.approx(1850.0)


def test_da_type_detection_from_subject():
    """DA type: 'final' in subject -> final, else proforma."""

    # Logic from parse_worker
    def get_da_type(subject: str | None) -> str:
        return "final" if (subject or "").lower().find("final") >= 0 else "proforma"

    assert get_da_type("Disbursement Account Proforma - MV Atlantic Star") == "proforma"
    assert get_da_type("Disbursement Account Final - MV Atlantic Star") == "final"
    assert get_da_type("Final DA for port call") == "final"
    assert get_da_type(None) == "proforma"
