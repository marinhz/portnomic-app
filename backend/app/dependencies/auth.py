import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import PLAN_LIMITS, settings
from app.services.limits import PREMIUM_PLANS
from app.dependencies.database import get_db
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import CurrentUser

bearer_scheme = HTTPBearer()


def _get_tenant_plan(tenant: Tenant | None) -> str:
    """Extract plan from tenant. Returns 'starter' if unknown."""
    if tenant is None:
        return "starter"
    if tenant.plan and tenant.plan in PLAN_LIMITS:
        return tenant.plan
    if tenant.settings and isinstance(tenant.settings, dict):
        plan = tenant.settings.get("plan")
        if plan in PLAN_LIMITS:
            return plan
    return "starter"


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id), User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    permissions = role.permissions if role else []

    admin_emails = [
        e.strip().lower() for e in settings.platform_admin_emails.split(",") if e.strip()
    ]
    is_platform_admin = user.email.lower() in admin_emails

    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    tenant_plan = _get_tenant_plan(tenant)

    role_name = role.name if role else None
    leakage_detector_enabled = tenant_plan in PREMIUM_PLANS
    return CurrentUser(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role_id=user.role_id,
        role_name=role_name,
        permissions=permissions,
        mfa_enabled=user.mfa_enabled,
        is_platform_admin=is_platform_admin,
        tenant_plan=tenant_plan,
        leakage_detector_enabled=leakage_detector_enabled,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
