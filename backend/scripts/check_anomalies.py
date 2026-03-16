#!/usr/bin/env python3
"""Quick check: list anomalies and DAs for demo tenant. Run from backend: python scripts/check_anomalies.py"""

import asyncio
import sys

sys.path.insert(0, ".")

from sqlalchemy import func, select

from app.database import async_session_factory
from app.models.anomaly import Anomaly
from app.models.disbursement_account import DisbursementAccount
from app.models.tenant import Tenant


async def main() -> None:
    async with async_session_factory() as db:
        r = await db.execute(select(Tenant).where(Tenant.slug == "demo"))
        tenant = r.scalar_one_or_none()
        if not tenant:
            print("No demo tenant found. Run: python -m app.seed")
            return

        tid = tenant.id
        print(f"Tenant: {tenant.name} (plan={tenant.plan})")
        print()

        # Count DAs
        r = await db.execute(
            select(func.count())
            .select_from(DisbursementAccount)
            .where(DisbursementAccount.tenant_id == tid)
        )
        da_count = r.scalar() or 0
        print(f"DAs: {da_count}")

        # Count anomalies
        r = await db.execute(
            select(func.count()).select_from(Anomaly).where(Anomaly.tenant_id == tid)
        )
        anom_count = r.scalar() or 0
        print(f"Anomalies: {anom_count}")

        if anom_count == 0:
            print()
            print("No anomalies. Run: python -m app.seed_leakage")
            return

        # List anomalies with DA ids
        r = await db.execute(
            select(Anomaly)
            .where(Anomaly.tenant_id == tid)
            .order_by(Anomaly.created_at.asc())
            .limit(20)
        )
        anomalies = list(r.scalars().all())
        print()
        print("Sample anomalies (da_id, rule_id, severity, line_item_ref):")
        for a in anomalies:
            print(f"  {a.da_id} | {a.rule_id} | {a.severity} | {a.line_item_ref}")


if __name__ == "__main__":
    asyncio.run(main())
