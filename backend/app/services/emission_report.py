"""Emission report service: fetch and manage emission reports."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.emission_report import EmissionReport


async def list_emission_reports(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    vessel_id: uuid.UUID | None = None,
    verification_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[EmissionReport], int]:
    """List emission reports for tenant with optional filters. Returns (reports, total)."""
    base = (
        select(EmissionReport)
        .where(EmissionReport.tenant_id == tenant_id)
        .options(selectinload(EmissionReport.vessel), selectinload(EmissionReport.fuel_entries))
    )
    count_base = select(EmissionReport).where(EmissionReport.tenant_id == tenant_id)

    if vessel_id is not None:
        base = base.where(EmissionReport.vessel_id == vessel_id)
        count_base = count_base.where(EmissionReport.vessel_id == vessel_id)
    if verification_status:
        base = base.where(EmissionReport.status == verification_status)
        count_base = count_base.where(EmissionReport.status == verification_status)
    if date_from is not None:
        base = base.where(EmissionReport.report_date >= date_from)
        count_base = count_base.where(EmissionReport.report_date >= date_from)
    if date_to is not None:
        base = base.where(EmissionReport.report_date <= date_to)
        count_base = count_base.where(EmissionReport.report_date <= date_to)

    total = (await db.execute(select(func.count()).select_from(count_base))).scalar() or 0
    stmt = (
        base.order_by(EmissionReport.report_date.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_emission_report(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    report_id: uuid.UUID,
) -> EmissionReport | None:
    """Fetch a single emission report by ID, tenant-scoped."""
    stmt = (
        select(EmissionReport)
        .where(
            EmissionReport.id == report_id,
            EmissionReport.tenant_id == tenant_id,
        )
        .options(selectinload(EmissionReport.fuel_entries))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_emission_report_by_email_id(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_id: uuid.UUID,
) -> EmissionReport | None:
    """Fetch emission report linked to a source email, if any."""
    stmt = (
        select(EmissionReport)
        .where(
            EmissionReport.email_id == email_id,
            EmissionReport.tenant_id == tenant_id,
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


__all__ = ["get_emission_report", "get_emission_report_by_email_id", "list_emission_reports"]
