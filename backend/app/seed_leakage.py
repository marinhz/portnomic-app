"""Seed Leakage Detector anomalies for demo/development.

Adds sample anomalies to existing DAs so the Leakage Detector UI can be tested.
Run after base seed + marketing seed: python -m app.seed && python -m app.seed_marketing && python -m app.seed_leakage

Or run alone if you already have DAs: python -m app.seed_leakage

Usage:
    cd backend && python -m app.seed_leakage
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.anomaly import Anomaly
from app.models.disbursement_account import DisbursementAccount
from app.models.email import Email
from app.models.tenant import Tenant

ANOMALY_SAMPLES = [
    {
        "line_item_ref": "Pilotage",
        "rule_id": "LD-001",
        "severity": "high",
        "invoiced_value": 1850.0,
        "expected_value": 1650.0,
        "description": "Service date on invoice (14-Mar 08:00) is before vessel ETA (15-Mar 06:00). Pilotage may have been charged for incorrect port call.",
        "raw_evidence": {"invoice_date": "2025-03-14T08:00:00Z", "eta": "2025-03-15T06:00:00Z"},
    },
    {
        "line_item_ref": "Berth hire",
        "rule_id": "LD-002",
        "severity": "critical",
        "invoiced_value": 2312.5,
        "expected_value": 2312.5,
        "description": "Duplicate charge: identical Berth hire line (18.5 hrs @ 125 USD) already present in DA for same port call.",
        "raw_evidence": {"duplicate_ref": "line_3", "amount": 2312.5},
    },
    {
        "line_item_ref": "Mooring/unmooring",
        "rule_id": "LD-003",
        "severity": "medium",
        "invoiced_value": 520.0,
        "expected_value": 420.0,
        "description": "Weekend/holiday rate (520 USD) charged but Port Call log shows service during standard hours (Wed 14-Mar 09:15–09:45). Expected standard rate: 420 USD.",
        "raw_evidence": {"service_time": "2025-03-14T09:15:00Z", "rate_type": "weekend"},
    },
    {
        "line_item_ref": "Port dues (per GRT)",
        "rule_id": "LD-004",
        "severity": "high",
        "invoiced_value": 10625.0,
        "expected_value": 10200.0,
        "description": "Invoiced quantity 12,500 GRT exceeds noon report figure (12,000 GRT). Variance: +4.2%. Expected: 12,000 × 0.85 = 10,200 USD.",
        "raw_evidence": {"invoiced_grt": 12500, "noon_report_grt": 12000, "rate": 0.85},
    },
    {
        "line_item_ref": "Agency fee",
        "rule_id": "LD-001",
        "severity": "low",
        "invoiced_value": 850.0,
        "expected_value": 750.0,
        "description": "Agency fee invoiced at 850 USD exceeds tariff (750 USD). Minor variance; verify if extras were agreed.",
        "raw_evidence": {"tariff_rate": 750, "invoiced": 850},
    },
]


async def seed_leakage(db: AsyncSession) -> None:
    """Add Leakage Detector anomalies to existing DAs."""
    result = await db.execute(select(Tenant).where(Tenant.slug == "demo"))
    tenant = result.scalar_one_or_none()
    if not tenant:
        print("Demo tenant not found. Run 'python -m app.seed' first.")
        return

    tenant_id = tenant.id

    das_result = await db.execute(
        select(DisbursementAccount)
        .where(DisbursementAccount.tenant_id == tenant_id)
        .order_by(DisbursementAccount.created_at.asc())
        .limit(6)
    )
    das_to_seed = list(das_result.scalars().all())

    emails_result = await db.execute(select(Email).where(Email.tenant_id == tenant_id).limit(1))
    default_email = emails_result.scalar_one_or_none()

    if not das_to_seed:
        print("No DAs found. Run 'python -m app.seed_marketing' first.")
        return

    if not default_email:
        print("No emails found. Run 'python -m app.seed_marketing' first.")
        return

    count = 0
    for i, da in enumerate(das_to_seed[:4]):
        idx1, idx2 = (i * 2) % len(ANOMALY_SAMPLES), (i * 2 + 1) % len(ANOMALY_SAMPLES)
        for sample in [ANOMALY_SAMPLES[idx1], ANOMALY_SAMPLES[idx2]]:
            a = Anomaly(
                tenant_id=tenant_id,
                email_id=default_email.id,
                da_id=da.id,
                port_call_id=da.port_call_id,
                rule_id=sample["rule_id"],
                severity=sample["severity"],
                line_item_ref=sample["line_item_ref"],
                invoiced_value=sample["invoiced_value"],
                expected_value=sample["expected_value"],
                description=sample["description"],
                raw_evidence=sample["raw_evidence"],
            )
            db.add(a)
            count += 1

    await db.commit()
    print(f"Created {count} Leakage Detector anomalies for {min(4, len(das_to_seed))} DAs.")
    print("  Open a DA in the app to see flagged line items and anomaly details.")


async def main() -> None:
    async with async_session_factory() as session:
        await seed_leakage(session)


if __name__ == "__main__":
    asyncio.run(main())
