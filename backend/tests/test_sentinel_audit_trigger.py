"""Tests for Sentinel audit trigger (Task 14.6)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database import async_session_factory
from app.models.email import Email
from app.models.emission_report import EmissionReport
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tenant import Tenant
from app.models.vessel import Vessel
from app.services.sentinel_audit_trigger import (
    _has_da_data,
    _has_noon_data,
    _has_sof_data,
    _is_relevant_for_sentinel,
    trigger_sentinel_audit_after_parse,
)


def test_has_da_data():
    """DA data detected from line_items in ai_raw_output."""
    assert _has_da_data({"line_items": [{"description": "Pilotage", "amount": 500}]}) is True
    assert _has_da_data(None) is False
    assert _has_da_data({}) is False
    assert _has_da_data({"line_items": []}) is False


def test_has_sof_data():
    """SOF data detected from sof_timestamps or port_log."""
    assert _has_sof_data({"sof_timestamps": {"tug_fast": "2026-03-11T10:00:00Z"}}) is True
    assert _has_sof_data({"port_log": {"pilot_on": "2026-03-11T10:00:00Z"}}) is True
    assert _has_sof_data(None) is False
    assert _has_sof_data({}) is False
    assert _has_sof_data({"line_items": []}) is False


def test_has_noon_data():
    """Noon data from emission_report."""
    report = MagicMock(spec=EmissionReport)
    assert _has_noon_data(report) is True
    assert _has_noon_data(None) is False


def test_is_relevant_for_sentinel():
    """Relevant when DA, SOF, or Noon data present."""
    assert _is_relevant_for_sentinel(ai_raw_output={"line_items": [{}]}, da=None, emission_report=None) is True
    assert (
        _is_relevant_for_sentinel(
            ai_raw_output={"sof_timestamps": {}},
            da=None,
            emission_report=None,
        )
        is True
    )
    assert (
        _is_relevant_for_sentinel(
            ai_raw_output={},
            da=None,
            emission_report=MagicMock(spec=EmissionReport),
        )
        is True
    )
    assert (
        _is_relevant_for_sentinel(
            ai_raw_output={},
            da=MagicMock(line_items=[{}]),
            emission_report=None,
        )
        is True
    )
    assert (
        _is_relevant_for_sentinel(
            ai_raw_output={},
            da=None,
            emission_report=None,
        )
        is False
    )


@pytest.mark.asyncio
async def test_trigger_skips_when_no_relevant_data():
    """Trigger returns None when email has no DA/SOF/Noon data."""
    async with async_session_factory() as db:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Test",
            slug=f"test-{uuid.uuid4().hex[:8]}",
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
            external_id="ext-1",
            ai_raw_output={"summary": "No relevant data"},
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        result = await trigger_sentinel_audit_after_parse(db, email, port_call.id)
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
                "line_items": [{"description": "Pilotage", "amount": 500}],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.sentinel_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)

            result = await trigger_sentinel_audit_after_parse(db, email, port_call.id)
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
                "line_items": [{"description": "Pilotage", "amount": 500}],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.sentinel_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=1)

            result = await trigger_sentinel_audit_after_parse(db, email, port_call.id)
            assert result is None
            mock_redis.set.assert_not_called()

        await db.rollback()


@pytest.mark.asyncio
async def test_trigger_runs_audit_and_sets_idempotency():
    """Trigger runs AuditEngine.compare_events and sets Redis idempotency key."""
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
            external_id="ext-4",
            ai_raw_output={
                "line_items": [{"description": "Pilotage", "amount": 500}],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        mock_report = MagicMock()
        mock_report.total_count = 2
        mock_report.discrepancies = []

        with patch("app.services.sentinel_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)
            mock_redis.set = AsyncMock()

            with patch(
                "app.services.sentinel_audit_trigger.AuditEngine",
            ) as mock_engine_class:
                mock_engine = MagicMock()
                mock_engine.compare_events = AsyncMock(return_value=mock_report)
                mock_engine_class.return_value = mock_engine

                result = await trigger_sentinel_audit_after_parse(db, email, port_call.id)

            assert result is not None
            assert result.total_count == 2
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert "shipflow:sentinel_audit:" in str(call_args[0][0])
            assert str(port_call.id) in str(call_args[0][0])
            assert str(email.id) in str(call_args[0][0])

        await db.rollback()


@pytest.mark.asyncio
async def test_trigger_failure_returns_none_non_blocking():
    """Sentinel failure returns None; does not raise — parse flow not blocked."""
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
            external_id="ext-fail",
            ai_raw_output={
                "line_items": [{"description": "Pilotage", "amount": 500}],
            },
            port_call_id=port_call.id,
        )
        db.add(email)
        await db.flush()

        with patch("app.services.sentinel_audit_trigger.redis_client") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=0)

            with patch(
                "app.services.sentinel_audit_trigger.AuditEngine",
            ) as mock_engine_class:
                mock_engine = MagicMock()
                mock_engine.compare_events = AsyncMock(
                    side_effect=TimeoutError("AIS timeout"),
                )
                mock_engine_class.return_value = mock_engine

                result = await trigger_sentinel_audit_after_parse(db, email, port_call.id)

            assert result is None
            mock_redis.set.assert_not_called()

        await db.rollback()
