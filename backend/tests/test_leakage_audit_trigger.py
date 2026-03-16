"""Tests for leakage audit trigger (Task 12.3)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.database import async_session_factory
from app.models.email import Email
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tenant import Tenant
from app.models.vessel import Vessel
from app.services.leakage_audit_trigger import (
    _is_financial_document,
    trigger_leakage_audit_after_parse,
)


def test_is_financial_document_with_line_items():
    """Financial document has non-empty line_items."""
    assert (
        _is_financial_document({"line_items": [{"description": "Pilotage", "amount": 500}]}) is True
    )
    assert _is_financial_document({"line_items": [{}]}) is True


def test_is_financial_document_without_line_items():
    """Non-financial or empty line_items is not a financial document."""
    assert _is_financial_document(None) is False
    assert _is_financial_document({}) is False
    assert _is_financial_document({"line_items": []}) is False
    assert _is_financial_document({"line_items": None}) is False
    assert _is_financial_document({"line_items": "invalid"}) is False


@pytest.mark.asyncio
async def test_trigger_skips_when_no_line_items():
    """Trigger returns None when email has no line_items."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test",
            slug=f"test-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        email = Email(
            tenant_id=tenant.id,
            external_id="ext-1",
            ai_raw_output={"line_items": []},
            port_call_id=None,
        )
        db.add(email)
        await db.flush()

        result = await trigger_leakage_audit_after_parse(db, email)
        assert result is None

        await db.rollback()


@pytest.mark.asyncio
async def test_trigger_skips_for_starter_plan():
    """Trigger skips when tenant is on Starter plan."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Starter Tenant",
            slug=f"starter-{uuid.uuid4().hex[:8]}",
            plan="starter",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="MV Test")
        db.add(vessel)
        await db.flush()

        port = Port(tenant_id=tenant.id, name="Rotterdam", code="NLRTM")
        db.add(port)
        await db.flush()

        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
            etd=datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc),
        )
        db.add(port_call)
        await db.flush()

        email = Email(
            tenant_id=tenant.id,
            external_id="ext-2",
            ai_raw_output={
                "line_items": [
                    {
                        "description": "Pilotage",
                        "amount": 500,
                        "service_date": "2026-03-11T10:00:00Z",
                    },
                ],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.leakage_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)

            result = await trigger_leakage_audit_after_parse(db, email)
            assert result is None
            mock_redis.set.assert_not_called()

        await db.rollback()


@pytest.mark.asyncio
async def test_trigger_skips_when_idempotency_key_exists():
    """Trigger skips when Redis idempotency key already exists."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Pro Tenant",
            slug=f"pro-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="MV Test")
        db.add(vessel)
        await db.flush()

        port = Port(tenant_id=tenant.id, name="Rotterdam", code="NLRTM")
        db.add(port)
        await db.flush()

        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
            etd=datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc),
        )
        db.add(port_call)
        await db.flush()

        email = Email(
            tenant_id=tenant.id,
            external_id="ext-3",
            ai_raw_output={
                "line_items": [
                    {
                        "description": "Pilotage",
                        "amount": 500,
                        "service_date": "2026-03-11T10:00:00Z",
                    },
                ],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.leakage_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=1)  # Key already exists

            result = await trigger_leakage_audit_after_parse(db, email)
            assert result is None
            mock_redis.set.assert_not_called()

        await db.rollback()


@pytest.mark.asyncio
async def test_trigger_runs_audit_and_sets_idempotency():
    """Trigger runs AuditService and sets Redis idempotency key for Professional plan."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Pro Tenant",
            slug=f"pro-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="MV Test")
        db.add(vessel)
        await db.flush()

        port = Port(tenant_id=tenant.id, name="Rotterdam", code="NLRTM")
        db.add(port)
        await db.flush()

        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
            etd=datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc),
        )
        db.add(port_call)
        await db.flush()

        # Service date before ETA -> LD-001 should flag
        email = Email(
            tenant_id=tenant.id,
            external_id="ext-4",
            ai_raw_output={
                "line_items": [
                    {
                        "description": "Pilotage",
                        "amount": 500,
                        "service_date": "2026-03-09T10:00:00Z",
                    },
                ],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.leakage_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)
            mock_redis.set = AsyncMock()

            result = await trigger_leakage_audit_after_parse(db, email)

            assert result is not None
            assert len(result) >= 1
            assert result[0].rule_id == "LD-001"
            assert email.audit_status == "completed"
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert "shipflow:leakage_audit:" in str(call_args[0][0])
            assert str(email.id) in str(call_args[0][0])

        await db.rollback()


@pytest.mark.asyncio
async def test_circuit_breaker_marks_pending_manual_review_on_audit_failure():
    """When run_audit fails, email/DA marked pending_manual_review; no idempotency key set."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Pro Tenant",
            slug=f"pro-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="MV Test")
        db.add(vessel)
        await db.flush()

        port = Port(tenant_id=tenant.id, name="Rotterdam", code="NLRTM")
        db.add(port)
        await db.flush()

        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
            etd=datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc),
        )
        db.add(port_call)
        await db.flush()

        email = Email(
            tenant_id=tenant.id,
            external_id="ext-circuit",
            ai_raw_output={
                "line_items": [
                    {
                        "description": "Pilotage",
                        "amount": 500,
                        "service_date": "2026-03-11T10:00:00Z",
                    },
                ],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.leakage_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)

            with patch(
                "app.services.leakage_audit_trigger.run_audit",
                new_callable=AsyncMock,
                side_effect=TimeoutError("LLM timeout"),
            ):
                result = await trigger_leakage_audit_after_parse(db, email)

            assert result is None
            assert email.audit_status == "pending_manual_review"
            mock_redis.set.assert_not_called()

        await db.rollback()


@pytest.mark.asyncio
async def test_circuit_breaker_sets_da_audit_status_when_da_provided():
    """When run_audit fails and DA is provided, both email and DA get pending_manual_review."""
    from app.models.disbursement_account import DisbursementAccount

    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Pro Tenant",
            slug=f"pro-{uuid.uuid4().hex[:8]}",
            plan="professional",
        )
        db.add(tenant)
        await db.flush()

        vessel = Vessel(tenant_id=tenant.id, name="MV Test")
        db.add(vessel)
        await db.flush()

        port = Port(tenant_id=tenant.id, name="Rotterdam", code="NLRTM")
        db.add(port)
        await db.flush()

        port_call = PortCall(
            tenant_id=tenant.id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=datetime(2026, 3, 10, 8, 0, 0, tzinfo=timezone.utc),
            etd=datetime(2026, 3, 12, 18, 0, 0, tzinfo=timezone.utc),
        )
        db.add(port_call)
        await db.flush()

        email = Email(
            tenant_id=tenant.id,
            external_id="ext-circuit-da",
            ai_raw_output={
                "line_items": [
                    {
                        "description": "Pilotage",
                        "amount": 500,
                        "service_date": "2026-03-11T10:00:00Z",
                    },
                ],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        da = DisbursementAccount(
            tenant_id=tenant.id,
            port_call_id=port_call.id,
            type="proforma",
            status="draft",
            line_items=[],
            totals={},
        )
        db.add(da)
        await db.flush()

        with patch("app.services.leakage_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)

            with patch(
                "app.services.leakage_audit_trigger.run_audit",
                new_callable=AsyncMock,
                side_effect=ConnectionError("API unreachable"),
            ):
                result = await trigger_leakage_audit_after_parse(db, email, da=da)

            assert result is None
            assert email.audit_status == "pending_manual_review"
            assert da.audit_status == "pending_manual_review"
            mock_redis.set.assert_not_called()

        await db.rollback()
