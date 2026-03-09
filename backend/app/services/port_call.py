import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.port_call import PortCall
from app.schemas.port_call import PortCallCreate, PortCallUpdate


async def list_port_calls(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    vessel_id: uuid.UUID | None = None,
    status: str | None = None,
) -> tuple[list[PortCall], int]:
    base = select(PortCall).where(PortCall.tenant_id == tenant_id)
    count_base = select(func.count()).select_from(PortCall).where(PortCall.tenant_id == tenant_id)

    if vessel_id is not None:
        base = base.where(PortCall.vessel_id == vessel_id)
        count_base = count_base.where(PortCall.vessel_id == vessel_id)
    if status is not None:
        base = base.where(PortCall.status == status)
        count_base = count_base.where(PortCall.status == status)

    total = (await db.execute(count_base)).scalar_one()

    q = (
        base.order_by(PortCall.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_port_call(
    db: AsyncSession, tenant_id: uuid.UUID, port_call_id: uuid.UUID
) -> PortCall | None:
    result = await db.execute(
        select(PortCall).where(
            PortCall.id == port_call_id, PortCall.tenant_id == tenant_id
        )
    )
    return result.scalar_one_or_none()


async def create_port_call(
    db: AsyncSession, tenant_id: uuid.UUID, data: PortCallCreate
) -> PortCall:
    port_call = PortCall(tenant_id=tenant_id, **data.model_dump())
    db.add(port_call)
    await db.flush()
    await db.refresh(port_call)
    return port_call


async def update_port_call(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    port_call_id: uuid.UUID,
    data: PortCallUpdate,
) -> PortCall | None:
    port_call = await get_port_call(db, tenant_id, port_call_id)
    if port_call is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(port_call, field, value)
    await db.flush()
    await db.refresh(port_call)
    return port_call
