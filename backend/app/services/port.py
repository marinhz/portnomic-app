import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.port import Port
from app.schemas.port import PortCreate, PortUpdate
from app.services.cache import cache_delete_pattern, cache_get, cache_set, make_cache_key


async def list_ports(
    db: AsyncSession, tenant_id: uuid.UUID, page: int = 1, per_page: int = 20
) -> tuple[list[Port], int]:
    base = select(Port).where(
        (Port.tenant_id == tenant_id) | (Port.tenant_id.is_(None))
    )
    count_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = count_result.scalar() or 0

    result = await db.execute(
        base.order_by(Port.name).offset((page - 1) * per_page).limit(per_page)
    )
    return list(result.scalars().all()), total


async def get_port(
    db: AsyncSession, tenant_id: uuid.UUID, port_id: uuid.UUID
) -> Port | None:
    cache_key = make_cache_key(str(tenant_id), "ports", str(port_id))
    cached = await cache_get(cache_key)
    if cached is not None:
        result = await db.execute(
            select(Port).where(
                Port.id == port_id,
                (Port.tenant_id == tenant_id) | (Port.tenant_id.is_(None)),
            )
        )
        return result.scalar_one_or_none()

    result = await db.execute(
        select(Port).where(
            Port.id == port_id,
            (Port.tenant_id == tenant_id) | (Port.tenant_id.is_(None)),
        )
    )
    port = result.scalar_one_or_none()
    if port:
        await cache_set(cache_key, {"id": str(port.id), "name": port.name, "code": port.code})
    return port


async def create_port(
    db: AsyncSession, tenant_id: uuid.UUID, data: PortCreate
) -> Port:
    port = Port(tenant_id=tenant_id, **data.model_dump())
    db.add(port)
    await db.flush()
    await db.refresh(port)
    await cache_delete_pattern(make_cache_key(str(tenant_id), "ports", "*"))
    return port


async def update_port(
    db: AsyncSession, tenant_id: uuid.UUID, port_id: uuid.UUID, data: PortUpdate
) -> Port | None:
    port = await get_port(db, tenant_id, port_id)
    if port is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(port, key, value)
    await db.flush()
    await db.refresh(port)
    await cache_delete_pattern(make_cache_key(str(tenant_id), "ports", "*"))
    return port
