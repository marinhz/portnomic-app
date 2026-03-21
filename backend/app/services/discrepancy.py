"""Discrepancy service for Sentinel Operational Gap Engine."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discrepancy import Discrepancy


async def list_discrepancies_for_port_call(
    db: AsyncSession, tenant_id: uuid.UUID, port_call_id: uuid.UUID
) -> list[Discrepancy]:
    """List discrepancies for a port call, tenant-scoped."""
    result = await db.execute(
        select(Discrepancy)
        .where(
            Discrepancy.port_call_id == port_call_id,
            Discrepancy.tenant_id == tenant_id,
        )
        .order_by(Discrepancy.created_at.desc())
    )
    return list(result.scalars().all())
