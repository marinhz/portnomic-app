"""Limits service for plan-based feature gating.

Enforces user, vessel, DA, and AI parse limits per tenant plan.
See docs/monetization-plan.md for plan details.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import PLAN_LIMITS, settings
from app.models.disbursement_account import DisbursementAccount
from app.models.parse_job import ParseJob
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vessel import Vessel

LimitType = Literal["users", "vessels", "das", "ai_parse", "ai_settings", "leakage_detector"]

UPGRADE_MESSAGES: dict[str, str] = {
    "users": "User limit reached. Upgrade your plan to add more users.",
    "vessels": "Vessel limit reached. Upgrade your plan to add more vessels.",
    "das": "Monthly DA limit reached. Upgrade your plan to generate more DAs.",
    "ai_parse": "Monthly AI parse limit reached. Upgrade your plan for more parses.",
    "ai_settings": "AI settings are available on Professional and Enterprise plans.",
    "leakage_detector": "Leakage Detector is available on Professional and Enterprise plans.",
}


async def require_leakage_detector(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    is_platform_admin: bool = False,
) -> None:
    """Require Professional or Enterprise plan for Leakage Detector.

    Raises HTTPException 403 with upgrade_required if tenant is on demo or starter.
    Platform admins bypass the plan check.
    """
    if is_platform_admin:
        return
    plan = await _get_tenant_plan(db, tenant_id)
    if plan not in PREMIUM_PLANS:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "upgrade_required",
                "message": UPGRADE_MESSAGES["leakage_detector"],
                "limit_type": "leakage_detector",
            },
        )


__all__ = [
    "check_user_limit",
    "check_vessel_limit",
    "check_da_limit",
    "check_ai_parse_limit",
    "require_premium_ai",
    "require_leakage_detector",
    "LimitResult",
    "raise_if_over_limit",
    "get_tenant_plan",
    "PREMIUM_PLANS",
]

PREMIUM_PLANS = frozenset({"professional", "enterprise"})


async def require_premium_ai(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    is_platform_admin: bool = False,
) -> None:
    """Require Professional or Enterprise plan for AI settings.

    Raises HTTPException 403 with upgrade_required if tenant is on demo or starter.
    Platform admins bypass the plan check (can manage AI settings for any tenant).
    Demo is always blocked (even in development). Starter blocked in production.
    """
    if is_platform_admin:
        return
    plan = await _get_tenant_plan(db, tenant_id)
    if plan == "demo":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "upgrade_required",
                "message": UPGRADE_MESSAGES["ai_settings"],
                "limit_type": "ai_settings",
            },
        )
    if settings.environment == "development" and plan in PREMIUM_PLANS:
        return
    if plan not in PREMIUM_PLANS:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "upgrade_required",
                "message": UPGRADE_MESSAGES["ai_settings"],
                "limit_type": "ai_settings",
            },
        )


class LimitResult:
    """Result of a limit check."""

    def __init__(
        self,
        allowed: bool,
        limit: int | None,
        current: int,
        plan: str,
    ) -> None:
        self.allowed = allowed
        self.limit = limit
        self.current = current
        self.plan = plan

    @property
    def upgrade_message(self) -> str:
        if self.limit is None:
            return ""
        return f"Plan limit reached ({self.current}/{self.limit}). Upgrade your plan to add more."


def raise_if_over_limit(result: LimitResult, limit_type: LimitType) -> None:
    """Raise HTTPException 403 with upgrade_required if over limit."""
    if not result.allowed:
        message = UPGRADE_MESSAGES.get(
            limit_type,
            result.upgrade_message or "Plan limit reached. Upgrade your plan.",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "upgrade_required",
                "message": message,
                "limit_type": limit_type,
            },
        )


async def get_tenant_plan(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Get tenant plan from plan column. Falls back to starter for legacy data."""
    return await _get_tenant_plan(db, tenant_id)


async def _get_tenant_plan(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Get tenant plan from plan column. Falls back to settings.plan for legacy data."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return "starter"
    if tenant.plan and tenant.plan in PLAN_LIMITS:
        return tenant.plan
    if tenant.settings and isinstance(tenant.settings, dict):
        plan = tenant.settings.get("plan")
        if plan in PLAN_LIMITS:
            return plan
    return "starter"


def _get_limit(plan: str, key: str) -> int | None:
    """Get limit for plan and key. None means unlimited."""
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])
    return limits.get(key)


async def check_user_limit(db: AsyncSession, tenant_id: uuid.UUID) -> LimitResult:
    """Check if tenant can add another user. Returns LimitResult."""
    plan = await _get_tenant_plan(db, tenant_id)
    limit = _get_limit(plan, "users")
    count_q = select(func.count()).select_from(User).where(User.tenant_id == tenant_id)
    current = (await db.execute(count_q)).scalar_one()
    allowed = limit is None or current < limit
    return LimitResult(allowed=allowed, limit=limit, current=current, plan=plan)


async def check_vessel_limit(db: AsyncSession, tenant_id: uuid.UUID) -> LimitResult:
    """Check if tenant can add another vessel. Returns LimitResult."""
    plan = await _get_tenant_plan(db, tenant_id)
    limit = _get_limit(plan, "vessels")
    count_q = select(func.count()).select_from(Vessel).where(Vessel.tenant_id == tenant_id)
    current = (await db.execute(count_q)).scalar_one()
    allowed = limit is None or current < limit
    return LimitResult(allowed=allowed, limit=limit, current=current, plan=plan)


def _month_start() -> datetime:
    """Start of current month in UTC."""
    now = datetime.now(UTC)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


async def check_da_limit(db: AsyncSession, tenant_id: uuid.UUID) -> LimitResult:
    """Check if tenant can generate another DA this month. Returns LimitResult."""
    plan = await _get_tenant_plan(db, tenant_id)
    limit = _get_limit(plan, "das_per_month")
    month_start = _month_start()
    count_q = (
        select(func.count())
        .select_from(DisbursementAccount)
        .where(
            DisbursementAccount.tenant_id == tenant_id,
            DisbursementAccount.created_at >= month_start,
        )
    )
    current = (await db.execute(count_q)).scalar_one()
    allowed = limit is None or current < limit
    return LimitResult(allowed=allowed, limit=limit, current=current, plan=plan)


async def check_ai_parse_limit(db: AsyncSession, tenant_id: uuid.UUID) -> LimitResult:
    """Check if tenant can run another AI parse this month. Returns LimitResult."""
    plan = await _get_tenant_plan(db, tenant_id)
    limit = _get_limit(plan, "ai_parses_per_month")
    month_start = _month_start()
    count_q = (
        select(func.count())
        .select_from(ParseJob)
        .where(
            ParseJob.tenant_id == tenant_id,
            ParseJob.created_at >= month_start,
        )
    )
    current = (await db.execute(count_q)).scalar_one()
    allowed = limit is None or current < limit
    return LimitResult(allowed=allowed, limit=limit, current=current, plan=plan)
