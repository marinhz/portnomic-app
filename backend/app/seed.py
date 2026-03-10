"""Seed script to create a default tenant, admin role, and admin user for development."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.port import Port
from app.models.role import Role
from app.models.tenant import Tenant
from app.models.user import User
from app.services.auth import hash_password

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ADMIN_ROLE_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
OPERATOR_ROLE_ID = uuid.UUID("00000000-0000-0000-0000-000000000020")
SUPER_ADMIN_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000030")
SUPER_ADMIN_EMAIL = "admin@portnomic.com"

ADMIN_PERMISSIONS = [
    "vessel:read",
    "vessel:write",
    "port_call:read",
    "port_call:write",
    "admin:users",
    "admin:roles",
    "billing:manage",
    "settings:write",
    "ai:parse",
    "da:read",
    "da:write",
    "da:approve",
    "da:send",
]
OPERATOR_PERMISSIONS = [
    "vessel:read",
    "vessel:write",
    "port_call:read",
    "port_call:write",
    "ai:parse",
    "da:read",
    "da:write",
]


async def seed(db: AsyncSession) -> None:
    existing_tenant = await db.execute(select(Tenant).where(Tenant.id == TENANT_ID))
    tenant = existing_tenant.scalar_one_or_none()
    if tenant:
        # Ensure demo tenant has enterprise plan (full access for admin@portnomic.com)
        if tenant.plan != "enterprise":
            tenant.plan = "enterprise"
            await db.commit()
            print("Demo tenant plan updated to enterprise (AI settings, full limits).")
        # Add super admin user for screenshots if missing
        existing_super = await db.execute(
            select(User).where(User.tenant_id == TENANT_ID, User.email == SUPER_ADMIN_EMAIL)
        )
        if existing_super.scalar_one_or_none():
            print("Seed data already exists, skipping.")
            return
        admin_role = await db.execute(
            select(Role).where(Role.tenant_id == TENANT_ID, Role.name == "Admin")
        )
        role = admin_role.scalar_one_or_none()
        if not role:
            print("Admin role not found. Run full seed first.")
            return
        super_admin_user = User(
            id=SUPER_ADMIN_USER_ID,
            tenant_id=TENANT_ID,
            email=SUPER_ADMIN_EMAIL,
            password_hash=hash_password("admin123"),
            role_id=role.id,
            is_active=True,
            mfa_enabled=False,
        )
        db.add(super_admin_user)
        await db.commit()
        print("Super admin user added for screenshots.")
        print("  admin@portnomic.com / admin123")
        return

    tenant = Tenant(id=TENANT_ID, name="Portnomic Demo", slug="demo", plan="enterprise")
    db.add(tenant)

    admin_role = Role(
        id=ADMIN_ROLE_ID,
        tenant_id=TENANT_ID,
        name="Admin",
        permissions=ADMIN_PERMISSIONS,
    )
    operator_role = Role(
        id=OPERATOR_ROLE_ID,
        tenant_id=TENANT_ID,
        name="Operator",
        permissions=OPERATOR_PERMISSIONS,
    )
    db.add_all([admin_role, operator_role])

    admin_user = User(
        tenant_id=TENANT_ID,
        email="admin@shipflow.ai",
        password_hash=hash_password("admin123"),
        role_id=ADMIN_ROLE_ID,
        is_active=True,
        mfa_enabled=False,
    )
    db.add(admin_user)

    super_admin_user = User(
        id=SUPER_ADMIN_USER_ID,
        tenant_id=TENANT_ID,
        email=SUPER_ADMIN_EMAIL,
        password_hash=hash_password("admin123"),
        role_id=ADMIN_ROLE_ID,
        is_active=True,
        mfa_enabled=False,
    )
    db.add(super_admin_user)

    sample_ports = [
        Port(
            tenant_id=TENANT_ID,
            name="Rotterdam",
            code="NLRTM",
            country="Netherlands",
            timezone="Europe/Amsterdam",
        ),
        Port(
            tenant_id=TENANT_ID,
            name="Singapore",
            code="SGSIN",
            country="Singapore",
            timezone="Asia/Singapore",
        ),
        Port(
            tenant_id=TENANT_ID,
            name="Shanghai",
            code="CNSHA",
            country="China",
            timezone="Asia/Shanghai",
        ),
        Port(
            tenant_id=TENANT_ID,
            name="Hamburg",
            code="DEHAM",
            country="Germany",
            timezone="Europe/Berlin",
        ),
        Port(
            tenant_id=TENANT_ID,
            name="Piraeus",
            code="GRPIR",
            country="Greece",
            timezone="Europe/Athens",
        ),
    ]
    db.add_all(sample_ports)

    await db.commit()
    print("Seed data created successfully!")
    print(f"  Tenant: Portnomic Demo ({TENANT_ID})")
    print("  Admin user: admin@shipflow.ai / admin123")
    print("  Super admin (screenshots): admin@portnomic.com / admin123")
    print("  Roles: Admin, Operator")
    print("  Ports: Rotterdam, Singapore, Shanghai, Hamburg, Piraeus")


async def main() -> None:
    async with async_session_factory() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
