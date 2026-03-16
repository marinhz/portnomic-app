import uuid
from datetime import datetime, timezone
from typing import NamedTuple

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.anomaly import Anomaly
from app.models.disbursement_account import VALID_TRANSITIONS, DisbursementAccount
from app.models.port_call import PortCall
from app.services.formula_engine import compute_line_items
from app.services.limits import check_da_limit, raise_if_over_limit
from app.services.tariff import get_active_tariff


class DAListRow(NamedTuple):
    """DA list row with optional has_anomalies (Leakage Detector feature)."""

    da: DisbursementAccount
    has_anomalies: bool | None  # None when feature not enabled


async def list_das(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    port_call_id: uuid.UUID | None = None,
    status: str | None = None,
    has_anomalies: bool | None = None,
    include_has_anomalies: bool = False,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[DAListRow], int]:
    """List DAs with optional has_anomalies filter and field.

    When include_has_anomalies is True, each row includes has_anomalies.
    When has_anomalies is True, filter to DAs with at least one Anomaly.
    """
    base = select(DisbursementAccount).where(DisbursementAccount.tenant_id == tenant_id)
    if port_call_id:
        base = base.where(DisbursementAccount.port_call_id == port_call_id)
    if status:
        base = base.where(DisbursementAccount.status == status)

    anomaly_exists = exists().where(
        Anomaly.tenant_id == tenant_id,
        Anomaly.da_id == DisbursementAccount.id,
    )
    if has_anomalies:
        base = base.where(anomaly_exists)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    q = (
        base.order_by(DisbursementAccount.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    das = list(result.scalars().all())

    if not include_has_anomalies:
        return [DAListRow(da=d, has_anomalies=None) for d in das], total

    # Compute has_anomalies for each DA
    da_ids = [d.id for d in das]
    anomaly_counts = await db.execute(
        select(Anomaly.da_id, func.count(Anomaly.id))
        .where(
            Anomaly.tenant_id == tenant_id,
            Anomaly.da_id.in_(da_ids),
        )
        .group_by(Anomaly.da_id)
    )
    da_has_anomalies = {row[0]: row[1] > 0 for row in anomaly_counts.all()}
    rows = [DAListRow(da=d, has_anomalies=da_has_anomalies.get(d.id, False)) for d in das]
    return rows, total


async def get_da(
    db: AsyncSession, tenant_id: uuid.UUID, da_id: uuid.UUID
) -> DisbursementAccount | None:
    result = await db.execute(
        select(DisbursementAccount).where(
            DisbursementAccount.id == da_id,
            DisbursementAccount.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def generate_da(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    port_call_id: uuid.UUID,
    da_type: str,
    parsed_line_items: list[dict] | None = None,
) -> DisbursementAccount:
    result = await check_da_limit(db, tenant_id)
    raise_if_over_limit(result, "das")

    pc = await db.execute(
        select(PortCall)
        .where(PortCall.id == port_call_id, PortCall.tenant_id == tenant_id)
        .options(selectinload(PortCall.vessel), selectinload(PortCall.port))
    )
    port_call = pc.scalar_one_or_none()
    if port_call is None:
        raise ValueError("Port call not found or does not belong to tenant")

    tariff = await get_active_tariff(db, tenant_id, port_call.port_id)

    formula_config = tariff.formula_config if tariff else {"items": [], "tax_rate": 0}
    vessel = port_call.vessel
    vessel_data = {
        "name": vessel.name if vessel else "",
        "imo": vessel.imo if vessel else "",
        "grt": 0,
        "nrt": 0,
    }
    port_call_data = {
        "eta": port_call.eta.isoformat() if port_call.eta else None,
        "etd": port_call.etd.isoformat() if port_call.etd else None,
    }

    line_items, totals = compute_line_items(
        formula_config, vessel_data, port_call_data, parsed_line_items
    )

    existing_count = (
        await db.execute(
            select(func.count())
            .select_from(DisbursementAccount)
            .where(
                DisbursementAccount.tenant_id == tenant_id,
                DisbursementAccount.port_call_id == port_call_id,
                DisbursementAccount.type == da_type,
            )
        )
    ).scalar_one()

    da = DisbursementAccount(
        tenant_id=tenant_id,
        port_call_id=port_call_id,
        tariff_id=tariff.id if tariff else None,
        version=existing_count + 1,
        type=da_type,
        status="draft",
        line_items=line_items,
        totals=totals,
        currency=totals.get("currency", "USD"),
    )
    db.add(da)
    await db.flush()
    await db.refresh(da)
    return da


def validate_transition(current_status: str, new_status: str) -> bool:
    allowed = VALID_TRANSITIONS.get(current_status, ())
    return new_status in allowed


async def approve_da(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    da_id: uuid.UUID,
    user_id: uuid.UUID,
) -> DisbursementAccount | None:
    da = await get_da(db, tenant_id, da_id)
    if da is None:
        return None
    if not validate_transition(da.status, "approved"):
        raise ValueError(f"Cannot approve DA in status '{da.status}'")

    da.status = "approved"
    da.approved_at = datetime.now(timezone.utc)
    da.approved_by = user_id
    await db.flush()
    await db.refresh(da)
    return da


async def mark_sent(
    db: AsyncSession,
    da_id: uuid.UUID,
) -> None:
    result = await db.execute(select(DisbursementAccount).where(DisbursementAccount.id == da_id))
    da = result.scalar_one_or_none()
    if da and validate_transition(da.status, "sent"):
        da.status = "sent"
        da.sent_at = datetime.now(timezone.utc)
        await db.flush()
