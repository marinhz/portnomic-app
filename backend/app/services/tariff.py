import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tariff import Tariff
from app.schemas.tariff import TariffCreate, TariffUpdate
from app.services.cache import cache_delete_pattern, cache_get, cache_set, make_cache_key

TARIFF_CACHE_TTL = 600  # 10 minutes for reference data


async def list_tariffs(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    port_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Tariff], int]:
    base = select(Tariff).where(Tariff.tenant_id == tenant_id)
    if port_id:
        base = base.where(Tariff.port_id == port_id)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    q = base.order_by(Tariff.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_tariff(
    db: AsyncSession, tenant_id: uuid.UUID, tariff_id: uuid.UUID
) -> Tariff | None:
    result = await db.execute(
        select(Tariff).where(Tariff.id == tariff_id, Tariff.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def get_active_tariff(
    db: AsyncSession, tenant_id: uuid.UUID, port_id: uuid.UUID, ref_date: date | None = None
) -> Tariff | None:
    if ref_date is None:
        ref_date = date.today()

    cache_key = make_cache_key(str(tenant_id), "tariffs", "active", str(port_id), str(ref_date))
    cached = await cache_get(cache_key)
    if cached is not None:
        return await get_tariff(db, tenant_id, uuid.UUID(cached["id"]))

    result = await db.execute(
        select(Tariff)
        .where(
            Tariff.tenant_id == tenant_id,
            Tariff.port_id == port_id,
            Tariff.valid_from <= ref_date,
            (Tariff.valid_to.is_(None)) | (Tariff.valid_to >= ref_date),
        )
        .order_by(Tariff.version.desc())
        .limit(1)
    )
    tariff = result.scalar_one_or_none()
    if tariff:
        await cache_set(cache_key, {"id": str(tariff.id)}, ttl=TARIFF_CACHE_TTL)
    return tariff


async def create_tariff(
    db: AsyncSession, tenant_id: uuid.UUID, data: TariffCreate
) -> Tariff:
    max_version = (
        await db.execute(
            select(func.coalesce(func.max(Tariff.version), 0))
            .where(Tariff.tenant_id == tenant_id, Tariff.port_id == data.port_id)
        )
    ).scalar_one()

    tariff = Tariff(
        tenant_id=tenant_id,
        version=max_version + 1,
        **data.model_dump(),
    )
    db.add(tariff)
    await db.flush()
    await db.refresh(tariff)
    await cache_delete_pattern(make_cache_key(str(tenant_id), "tariffs", "*"))
    return tariff


async def update_tariff(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    tariff_id: uuid.UUID,
    data: TariffUpdate,
) -> Tariff | None:
    tariff = await get_tariff(db, tenant_id, tariff_id)
    if tariff is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tariff, field, value)
    await db.flush()
    await db.refresh(tariff)
    await cache_delete_pattern(make_cache_key(str(tenant_id), "tariffs", "*"))
    return tariff
