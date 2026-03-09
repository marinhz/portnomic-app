import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.user import User
from app.schemas.admin import RoleCreate, RoleUpdate, UserCreate, UserUpdate
from app.services.auth import hash_password
from app.services.limits import check_user_limit, raise_if_over_limit


async def list_users(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[User], int]:
    count_q = (
        select(func.count()).select_from(User).where(User.tenant_id == tenant_id)
    )
    total = (await db.execute(count_q)).scalar_one()

    q = (
        select(User)
        .where(User.tenant_id == tenant_id)
        .order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def create_user(
    db: AsyncSession, tenant_id: uuid.UUID, data: UserCreate
) -> User:
    result = await check_user_limit(db, tenant_id)
    raise_if_over_limit(result, "users")

    user = User(
        tenant_id=tenant_id,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=data.role_id,
        mfa_enabled=data.mfa_enabled,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user(
    db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    data: UserUpdate,
) -> User | None:
    user = await get_user(db, tenant_id, user_id)
    if user is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def list_roles(
    db: AsyncSession, tenant_id: uuid.UUID
) -> list[Role]:
    result = await db.execute(
        select(Role)
        .where(Role.tenant_id == tenant_id)
        .order_by(Role.created_at.desc())
    )
    return list(result.scalars().all())


async def get_role(
    db: AsyncSession, tenant_id: uuid.UUID, role_id: uuid.UUID
) -> Role | None:
    result = await db.execute(
        select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def create_role(
    db: AsyncSession, tenant_id: uuid.UUID, data: RoleCreate
) -> Role:
    role = Role(
        tenant_id=tenant_id,
        name=data.name,
        permissions=data.permissions,
    )
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


async def update_role(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    role_id: uuid.UUID,
    data: RoleUpdate,
    actor_permissions: list[str] | None = None,
) -> Role | None:
    """Update role. If actor_permissions is provided, restricts new permissions to those the actor has."""
    role = await get_role(db, tenant_id, role_id)
    if role is None:
        return None

    updates = data.model_dump(exclude_unset=True)
    if "permissions" in updates and actor_permissions is not None:
        # Prevent privilege escalation: actor cannot grant permissions they lack
        if "*" not in actor_permissions:
            for perm in updates["permissions"]:
                if perm not in actor_permissions:
                    raise ValueError(
                        f"Cannot grant permission '{perm}'; you do not have this permission"
                    )

    for field, value in updates.items():
        setattr(role, field, value)
    await db.flush()
    await db.refresh(role)
    return role
