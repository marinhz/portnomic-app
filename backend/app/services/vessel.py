import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vessel import Vessel
from app.schemas.vessel import VesselCreate, VesselUpdate
from app.services.limits import check_vessel_limit, raise_if_over_limit


async def list_vessels(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Vessel], int]:
    count_q = select(func.count()).select_from(Vessel).where(Vessel.tenant_id == tenant_id)
    total = (await db.execute(count_q)).scalar_one()

    q = (
        select(Vessel)
        .where(Vessel.tenant_id == tenant_id)
        .order_by(Vessel.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_vessel(db: AsyncSession, tenant_id: uuid.UUID, vessel_id: uuid.UUID) -> Vessel | None:
    result = await db.execute(
        select(Vessel).where(Vessel.id == vessel_id, Vessel.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def create_vessel(db: AsyncSession, tenant_id: uuid.UUID, data: VesselCreate) -> Vessel:
    result = await check_vessel_limit(db, tenant_id)
    raise_if_over_limit(result, "vessels")

    vessel = Vessel(tenant_id=tenant_id, **data.model_dump())
    db.add(vessel)
    await db.flush()
    await db.refresh(vessel)
    return vessel


async def update_vessel(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    vessel_id: uuid.UUID,
    data: VesselUpdate,
) -> Vessel | None:
    vessel = await get_vessel(db, tenant_id, vessel_id)
    if vessel is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(vessel, field, value)
    await db.flush()
    await db.refresh(vessel)
    return vessel
