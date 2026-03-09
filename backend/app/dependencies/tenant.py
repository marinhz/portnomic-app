import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.tenant import Tenant
from app.schemas.auth import CurrentUser


async def get_tenant_id(
    current_user: CurrentUser = Depends(get_current_user),
) -> uuid.UUID:
    return current_user.tenant_id


async def require_valid_tenant(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant not found or access denied",
        )
    return tenant_id
