import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import TenantUpdate
from app.services.auth import hash_password

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
RESERVED_SLUGS = frozenset({"admin", "platform", "api", "system", "root", "shipflow"})

DEFAULT_ADMIN_PERMISSIONS = [
    "vessel:read", "vessel:write",
    "port_call:read", "port_call:write",
    "admin:users", "admin:roles",
    "billing:manage",
    "settings:write",
    "ai:parse",
    "da:read", "da:write", "da:approve", "da:send",
]
DEFAULT_VIEWER_PERMISSIONS = [
    "vessel:read",
    "port_call:read",
    "da:read",
]


async def create_tenant(
    db: AsyncSession,
    name: str,
    slug: str,
    settings: dict | None = None,
    initial_admin_email: str | None = None,
    initial_admin_password: str | None = None,
) -> Tenant:
    slug_lower = slug.lower().strip()
    if slug_lower in RESERVED_SLUGS:
        raise ValueError(f"Slug '{slug_lower}' is reserved")
    if not SLUG_PATTERN.match(slug_lower):
        raise ValueError("Slug must be lowercase, alphanumeric with hyphens (e.g. acme-shipping)")

    existing = await db.execute(select(Tenant).where(Tenant.slug == slug_lower))
    if existing.scalar_one_or_none():
        raise ValueError(f"Tenant with slug '{slug_lower}' already exists")

    tenant = Tenant(name=name, slug=slug_lower, settings=settings or {})
    db.add(tenant)
    await db.flush()

    admin_role = Role(
        tenant_id=tenant.id,
        name="Admin",
        permissions=DEFAULT_ADMIN_PERMISSIONS,
    )
    viewer_role = Role(
        tenant_id=tenant.id,
        name="Viewer",
        permissions=DEFAULT_VIEWER_PERMISSIONS,
    )
    db.add_all([admin_role, viewer_role])
    await db.flush()

    if initial_admin_email and initial_admin_password:
        admin_user = User(
            tenant_id=tenant.id,
            email=initial_admin_email.lower().strip(),
            password_hash=hash_password(initial_admin_password),
            role_id=admin_role.id,
            is_active=True,
            mfa_enabled=False,
        )
        db.add(admin_user)

    await db.refresh(tenant)
    return tenant


async def list_tenants(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Tenant], int]:
    count_q = select(func.count()).select_from(Tenant)
    total = (await db.execute(count_q)).scalar_one()

    q = (
        select(Tenant)
        .order_by(Tenant.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    return result.scalar_one_or_none()


async def update_tenant(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: TenantUpdate,
) -> Tenant | None:
    tenant = await get_tenant(db, tenant_id)
    if tenant is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    await db.flush()
    await db.refresh(tenant)
    return tenant
