"""Seed Sentinel dummy data for marketing screenshots.

Creates MV Portnomic Voyager port call at Rotterdam with SOF, DA (overcharges),
EmissionReport, and runs AuditEngine to populate discrepancies.

Data matches sentinel-test-suite-data-spec.md for S-001 (tug) + S-002 (berthage) alerts.

Usage:
    cd backend && python -m app.seed && python -m app.seed_marketing && python -m app.seed_sentinel

Prerequisites:
    - Run migrations if needed: alembic upgrade head
    - Demo tenant + Rotterdam port + marketing seed must exist first.
"""

import asyncio
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.disbursement_account import DisbursementAccount
from app.models.email import Email
from app.models.emission_report import EmissionReport, FuelEntry
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tariff import Tariff
from app.models.tenant import Tenant
from app.models.vessel import Vessel
from app.services.sentinel import AuditEngine

# Port call: MV Portnomic Voyager, Rotterdam, ETA/ETD per spec
ETA = datetime(2026, 3, 15, 9, 0, 0, tzinfo=timezone.utc)  # 10:00 LT Rotterdam
ETD = datetime(2026, 3, 16, 13, 0, 0, tzinfo=timezone.utc)  # 14:00 LT Rotterdam

# SOF timestamps (1h tug actual, pilot 1h)
SOF_TIMESTAMPS = {
    "tug_fast": "2026-03-15T07:30:00Z",
    "tug_off": "2026-03-15T08:30:00Z",
    "pilot_on": "2026-03-15T08:00:00Z",
    "pilot_off": "2026-03-15T09:00:00Z",
}

# DA line items: intentional overcharges (3h tug vs 1h actual, 3 days berth vs ~1.17 actual)
DA_LINE_ITEMS = [
    {
        "description": "Tugboat charges",
        "quantity": 3.0,
        "amount": 2550,
        "service_date": "2026-03-15T07:30:00Z",
    },
    {
        "description": "Berthage / Quay dues",
        "quantity": 3.0,
        "amount": 3300,
        "service_date": "2026-03-15T09:00:00Z",
    },
    {
        "description": "Pilotage fee",
        "quantity": 1.0,
        "amount": 900,
        "service_date": "2026-03-15T08:00:00Z",
    },
]


async def seed_sentinel(db: AsyncSession) -> None:
    """Create Sentinel marketing data: port call, SOF, DA, noon report, run audit."""
    result = await db.execute(select(Tenant).where(Tenant.slug == "demo"))
    tenant = result.scalar_one_or_none()
    if not tenant:
        print("Demo tenant not found. Run 'python -m app.seed' first.")
        return

    tenant_id = tenant.id

    # Idempotent: skip if Sentinel SOF already exists
    existing = await db.execute(
        select(Email).where(
            Email.tenant_id == tenant_id,
            Email.external_id == "sentinel-marketing-sof-001",
        )
    )
    if existing.scalar_one_or_none():
        print("Sentinel marketing data already exists (sentinel-marketing-sof-001). Skipping.")
        return

    # Get Rotterdam
    port_result = await db.execute(
        select(Port).where(Port.tenant_id == tenant_id, Port.code == "NLRTM")
    )
    port = port_result.scalar_one_or_none()
    if not port:
        print("Rotterdam port not found. Run 'python -m app.seed_marketing' first.")
        return

    # Get or create MV Portnomic Voyager
    vessel_result = await db.execute(
        select(Vessel).where(Vessel.tenant_id == tenant_id, Vessel.name == "MV Portnomic Voyager")
    )
    vessel = vessel_result.scalar_one_or_none()
    if not vessel:
        vessel = Vessel(
            tenant_id=tenant_id,
            name="MV Portnomic Voyager",
            imo="9876543",
            mmsi="311000456",
            vessel_type="Container Ship",
            flag="Liberia",
            allowed_fuel_types=["VLSFO", "MDO"],
        )
        db.add(vessel)
        await db.flush()
        print("  Created vessel: MV Portnomic Voyager")

    # Get tariff for Rotterdam
    tariff_result = await db.execute(
        select(Tariff).where(Tariff.tenant_id == tenant_id, Tariff.port_id == port.id).limit(1)
    )
    tariff = tariff_result.scalar_one_or_none()

    # Create Sentinel port call
    pc = PortCall(
        tenant_id=tenant_id,
        vessel_id=vessel.id,
        port_id=port.id,
        eta=ETA,
        etd=ETD,
        status="completed",
    )
    db.add(pc)
    await db.flush()
    print(f"  Created port call: MV Portnomic Voyager @ Rotterdam ({pc.id})")

    # Create SOF email (Statement of Facts)
    sof_email = Email(
        tenant_id=tenant_id,
        port_call_id=pc.id,
        external_id="sentinel-marketing-sof-001",
        subject="Statement of Facts - MV Portnomic Voyager - Rotterdam 15-16 Mar 2026",
        sender="port.ops@rotterdam.nl",
        body_text=(
            "Statement of Facts\n"
            "Vessel: MV Portnomic Voyager | Port: Rotterdam ECT Delta Terminal\n"
            "Tug Fast: 08:30 | Cast off: 09:30 | First Line Ashore: 10:00 | Unberthed: 14:00"
        ),
        processing_status="completed",
        ai_raw_output={"sof_timestamps": SOF_TIMESTAMPS},
        received_at=ETA,
    )
    db.add(sof_email)
    await db.flush()
    print("  Created SOF email with tug/pilot timestamps")

    # Create DA with overcharges
    totals = {"subtotal": 6750, "tax": 0, "total": 6750, "currency": "EUR"}
    da = DisbursementAccount(
        tenant_id=tenant_id,
        port_call_id=pc.id,
        tariff_id=tariff.id if tariff else None,
        version=1,
        type="final",
        status="pending_approval",
        line_items=DA_LINE_ITEMS,
        totals=totals,
        currency="EUR",
    )
    db.add(da)
    await db.flush()
    print("  Created DA with tug/berthage/pilot line items (intentional overcharges)")

    # Create EmissionReport + FuelEntry (noon report, at_berth — no S-003)
    er = EmissionReport(
        tenant_id=tenant_id,
        vessel_id=vessel.id,
        port_call_id=pc.id,
        report_date=date(2026, 3, 16),
        distance_nm=None,
        status="verified",
        anomaly_flags=None,
    )
    db.add(er)
    await db.flush()
    fe = FuelEntry(
        emission_report_id=er.id,
        fuel_type="VLSFO",
        consumption_mt=12.5,
        operational_status="at_berth",
    )
    db.add(fe)
    await db.flush()
    print("  Created EmissionReport (noon report, 12.5 MT at berth)")

    # Run Sentinel audit
    engine = AuditEngine(db, tenant_id)
    report = await engine.compare_events(pc.id)
    print(f"  Sentinel audit: {report.total_count} discrepancy(ies)")
    for d in report.discrepancies:
        desc = (d.description or "")[:70]
        print(f"    [{d.rule_id}] {d.severity}: {desc}...")

    await db.commit()
    print("Sentinel seed completed!")
    print("  Port call ID for screenshots:", pc.id)
    print("  Login: admin@portnomic.com / admin123")


async def main() -> None:
    async with async_session_factory() as session:
        await seed_sentinel(session)


if __name__ == "__main__":
    asyncio.run(main())
