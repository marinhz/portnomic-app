import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parse_job import ParseJob


async def get_parse_job(
    db: AsyncSession, tenant_id: uuid.UUID, job_id: uuid.UUID
) -> ParseJob | None:
    result = await db.execute(
        select(ParseJob).where(ParseJob.id == job_id, ParseJob.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def list_parse_jobs_for_email(
    db: AsyncSession, tenant_id: uuid.UUID, email_id: uuid.UUID
) -> list[ParseJob]:
    result = await db.execute(
        select(ParseJob)
        .where(ParseJob.tenant_id == tenant_id, ParseJob.email_id == email_id)
        .order_by(ParseJob.created_at.desc())
    )
    return list(result.scalars().all())
