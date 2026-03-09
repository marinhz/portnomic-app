import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email
from app.schemas.email import EmailCreate


async def list_emails(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    status_filter: str | None = None,
) -> tuple[list[Email], int]:
    base = select(Email).where(Email.tenant_id == tenant_id)
    count_base = select(func.count()).select_from(Email).where(Email.tenant_id == tenant_id)

    if status_filter:
        base = base.where(Email.processing_status == status_filter)
        count_base = count_base.where(Email.processing_status == status_filter)

    total = (await db.execute(count_base)).scalar_one()
    q = base.order_by(Email.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_email(
    db: AsyncSession, tenant_id: uuid.UUID, email_id: uuid.UUID
) -> Email | None:
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def get_email_by_external_id(
    db: AsyncSession, tenant_id: uuid.UUID, external_id: str
) -> Email | None:
    result = await db.execute(
        select(Email).where(
            Email.tenant_id == tenant_id, Email.external_id == external_id
        )
    )
    return result.scalar_one_or_none()


async def create_email(
    db: AsyncSession, tenant_id: uuid.UUID, data: EmailCreate
) -> Email:
    email = Email(tenant_id=tenant_id, **data.model_dump())
    db.add(email)
    await db.flush()
    await db.refresh(email)
    return email


async def delete_email(
    db: AsyncSession, tenant_id: uuid.UUID, email_id: uuid.UUID
) -> bool:
    """Delete an email and its parse_jobs (cascade). Returns True if deleted, False if not found."""
    result = await db.execute(
        text("DELETE FROM emails WHERE id = :id AND tenant_id = :tenant_id"),
        {"id": email_id, "tenant_id": tenant_id},
    )
    await db.flush()
    return result.rowcount > 0


async def update_email_status(
    db: AsyncSession,
    email_id: uuid.UUID,
    *,
    processing_status: str | None = None,
    ai_raw_output: dict | None = None,
    error_reason: str | None = None,
    prompt_version: str | None = None,
    port_call_id: uuid.UUID | None = None,
    increment_retry: bool = False,
) -> Email | None:
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    if email is None:
        return None

    if processing_status is not None:
        email.processing_status = processing_status
    if ai_raw_output is not None:
        email.ai_raw_output = ai_raw_output
    if error_reason is not None:
        email.error_reason = error_reason
    if prompt_version is not None:
        email.prompt_version = prompt_version
    if port_call_id is not None:
        email.port_call_id = port_call_id
    if increment_retry:
        email.retry_count += 1

    await db.flush()
    await db.refresh(email)
    return email
