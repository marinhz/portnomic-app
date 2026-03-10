"""Seed marketing data: vessels, port calls, tariffs, DAs, emission reports,
emails, and email integrations (MailConnection).

Populates the demo tenant with realistic data for marketing screenshots.
Run after base seed: python -m app.seed && python -m app.seed_marketing

Usage:
    cd backend && python -m app.seed_marketing
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.disbursement_account import DisbursementAccount
from app.models.email import Email
from app.models.emission_report import EmissionReport, FuelEntry
from app.models.mail_connection import MailConnection
from app.models.port import Port
from app.models.port_call import PortCall
from app.models.tariff import Tariff
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vessel import Vessel
from app.services.mail_connection import encrypt_credentials

# Realistic vessel data for maritime marketing
VESSELS = [
    {
        "name": "MSC Gulsun",
        "imo": "9855811",
        "mmsi": "353136000",
        "vessel_type": "Container Ship",
        "flag": "Panama",
    },
    {
        "name": "Ever Given",
        "imo": "9811000",
        "mmsi": "353136000",
        "vessel_type": "Container Ship",
        "flag": "Panama",
    },
    {
        "name": "HMM Oslo",
        "imo": "9864918",
        "mmsi": "440123000",
        "vessel_type": "Container Ship",
        "flag": "Liberia",
    },
    {
        "name": "CMA CGM Antoine de Saint Exupery",
        "imo": "9778235",
        "mmsi": "229256000",
        "vessel_type": "Container Ship",
        "flag": "Malta",
    },
    {
        "name": "Pacific Voyager",
        "imo": "9123456",
        "mmsi": "538009123",
        "vessel_type": "Bulk Carrier",
        "flag": "Marshall Islands",
    },
    {
        "name": "Nordic Spirit",
        "imo": "9234567",
        "mmsi": "257123000",
        "vessel_type": "Ro-Ro Cargo",
        "flag": "Norway",
    },
    {
        "name": "Atlantic Star",
        "imo": "9345678",
        "mmsi": "311000123",
        "vessel_type": "General Cargo",
        "flag": "Bahamas",
    },
    {
        "name": "Blue Horizon",
        "imo": "9456789",
        "mmsi": "636015432",
        "vessel_type": "Chemical Tanker",
        "flag": "Liberia",
    },
]

# Tariff formula items (typical port charges)
TARIFF_ITEMS = [
    {"description": "Pilotage", "type": "per_call", "rate": 1850.0, "currency": "USD"},
    {"description": "Port dues (per GRT)", "type": "per_ton", "rate": 0.85, "currency": "USD"},
    {"description": "Berth hire", "type": "per_hour", "rate": 125.0, "currency": "USD"},
    {"description": "Mooring/unmooring", "type": "per_call", "rate": 420.0, "currency": "USD"},
    {"description": "Agency fee", "type": "fixed", "rate": 750.0, "currency": "USD"},
]

DA_LINE_ITEMS_SAMPLE = [
    {
        "description": "Pilotage",
        "quantity": 1.0,
        "unit_price": 1850.0,
        "amount": 1850.0,
        "currency": "USD",
    },
    {
        "description": "Port dues (per GRT)",
        "quantity": 12500.0,
        "unit_price": 0.85,
        "amount": 10625.0,
        "currency": "USD",
    },
    {
        "description": "Berth hire",
        "quantity": 18.5,
        "unit_price": 125.0,
        "amount": 2312.5,
        "currency": "USD",
    },
    {
        "description": "Mooring/unmooring",
        "quantity": 1.0,
        "unit_price": 420.0,
        "amount": 420.0,
        "currency": "USD",
    },
    {
        "description": "Agency fee",
        "quantity": 1.0,
        "unit_price": 750.0,
        "amount": 750.0,
        "currency": "USD",
    },
]


async def seed_marketing(db: AsyncSession) -> None:
    # Resolve demo tenant
    result = await db.execute(select(Tenant).where(Tenant.slug == "demo"))
    tenant = result.scalar_one_or_none()
    if not tenant:
        print("Demo tenant not found. Run 'python -m app.seed' first.")
        return

    tenant_id = tenant.id
    print(f"Seeding marketing data for tenant: {tenant.name} ({tenant_id})")

    # Get ports by code
    port_result = await db.execute(
        select(Port).where(Port.tenant_id == tenant_id).order_by(Port.code)
    )
    ports = list(port_result.scalars().all())
    if not ports:
        print("No ports found. Run base seed first.")
        return

    print(f"  Found {len(ports)} ports: {', '.join(p.code for p in ports)}")

    # Create vessels
    vessels: list[Vessel] = []
    for v_data in VESSELS:
        v = Vessel(
            tenant_id=tenant_id,
            name=v_data["name"],
            imo=v_data["imo"],
            mmsi=v_data["mmsi"],
            vessel_type=v_data["vessel_type"],
            flag=v_data["flag"],
            allowed_fuel_types=["VLSFO", "LNG", "MDO"],
        )
        db.add(v)
        vessels.append(v)
    await db.flush()
    print(f"  Created {len(vessels)} vessels")

    # Create port calls (spread across vessels and ports, various statuses)
    now = datetime.now(timezone.utc)
    port_calls: list[PortCall] = []
    statuses = ["scheduled", "arrived", "departed", "completed"]

    for i, vessel in enumerate(vessels):
        port = ports[i % len(ports)]
        days_ago = (i * 3) % 14
        eta = now - timedelta(days=days_ago, hours=12)
        etd = eta + timedelta(hours=18 + (i % 12))
        status = statuses[i % len(statuses)]

        pc = PortCall(
            tenant_id=tenant_id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=eta,
            etd=etd,
            status=status,
        )
        db.add(pc)
        port_calls.append(pc)

    # Extra port calls for more variety
    for i in range(4):
        vessel = vessels[(i + 2) % len(vessels)]
        port = ports[(i + 3) % len(ports)]
        days_ahead = i + 1
        eta = now + timedelta(days=days_ahead)
        etd = eta + timedelta(hours=20)

        pc = PortCall(
            tenant_id=tenant_id,
            vessel_id=vessel.id,
            port_id=port.id,
            eta=eta,
            etd=etd,
            status="scheduled",
        )
        db.add(pc)
        port_calls.append(pc)

    await db.flush()
    print(f"  Created {len(port_calls)} port calls")

    # Create tariffs (one per port)
    tariffs: list[Tariff] = []
    valid_from = date.today() - timedelta(days=90)
    valid_to = date.today() + timedelta(days=365)

    for port in ports:
        t = Tariff(
            tenant_id=tenant_id,
            port_id=port.id,
            name=f"{port.name} Standard Tariff 2025",
            version=1,
            formula_config={"items": TARIFF_ITEMS, "tax_rate": 0.0, "currency": "USD"},
            valid_from=valid_from,
            valid_to=valid_to,
        )
        db.add(t)
        tariffs.append(t)
    await db.flush()
    print(f"  Created {len(tariffs)} tariffs")

    # Create disbursement accounts (proforma and final, various statuses)
    da_statuses = ["draft", "pending_approval", "approved", "sent"]
    admin_result = await db.execute(select(User).where(User.tenant_id == tenant_id).limit(1))
    admin_user = admin_result.scalar_one_or_none()
    admin_id = admin_user.id if admin_user else None

    for i, pc in enumerate(port_calls[:12]):
        tariff = next((t for t in tariffs if t.port_id == pc.port_id), tariffs[0])
        da_type = "proforma" if i % 2 == 0 else "final"
        status = da_statuses[i % len(da_statuses)]

        subtotal = sum(li["amount"] for li in DA_LINE_ITEMS_SAMPLE)
        totals = {"subtotal": subtotal, "tax": 0.0, "total": subtotal, "currency": "USD"}

        da = DisbursementAccount(
            tenant_id=tenant_id,
            port_call_id=pc.id,
            tariff_id=tariff.id,
            version=1,
            type=da_type,
            status=status,
            line_items=DA_LINE_ITEMS_SAMPLE,
            totals=totals,
            currency="USD",
        )
        if status == "approved" and admin_id:
            da.approved_at = now - timedelta(days=i)
            da.approved_by = admin_id
        elif status == "sent" and admin_id:
            da.approved_at = now - timedelta(days=i + 1)
            da.approved_by = admin_id
            da.sent_at = now - timedelta(days=i)
        db.add(da)

    await db.flush()
    print("  Created 12 disbursement accounts")

    # Create emission reports with fuel entries
    fuel_types = ["VLSFO", "LNG", "MDO"]
    operational_statuses = ["at_berth", "at_anchor", "cruising", "maneuvering"]

    for i, vessel in enumerate(vessels[:6]):
        pc = port_calls[i] if i < len(port_calls) else port_calls[0]
        report_date = date.today() - timedelta(days=7 + i)

        er = EmissionReport(
            tenant_id=tenant_id,
            vessel_id=vessel.id,
            port_call_id=pc.id,
            report_date=report_date,
            distance_nm=1250.0 + (i * 200),
            status="verified",
            anomaly_flags=None,
        )
        db.add(er)
        await db.flush()

        # Add 2-3 fuel entries per report
        for j in range(2 + (i % 2)):
            fe = FuelEntry(
                emission_report_id=er.id,
                fuel_type=fuel_types[j % len(fuel_types)],
                consumption_mt=45.5 + (i * 3.2) + (j * 1.5),
                operational_status=operational_statuses[j % len(operational_statuses)],
            )
            db.add(fe)

    print("  Created 6 emission reports with fuel entries")

    # Create email integrations (MailConnection) - for Settings > Integrations screenshots
    conn_result = await db.execute(
        select(MailConnection).where(MailConnection.tenant_id == tenant_id)
    )
    existing_conns = list(conn_result.scalars().all())
    if not existing_conns:
        # Placeholder credentials for display only (sync would fail)
        placeholder_creds = encrypt_credentials(
            {"email": "ops@agency.com", "access_token": "x", "refresh_token": "y"}
        )
        integrations = [
            MailConnection(
                tenant_id=tenant_id,
                provider="gmail",
                display_email="ops@agency.com",
                encrypted_credentials=placeholder_creds,
                status="connected",
                last_sync_at=now - timedelta(minutes=15),
            ),
            MailConnection(
                tenant_id=tenant_id,
                provider="outlook",
                display_email="agency.ops@outlook.com",
                encrypted_credentials=placeholder_creds,
                status="connected",
                last_sync_at=now - timedelta(hours=1),
            ),
            MailConnection(
                tenant_id=tenant_id,
                provider="imap",
                display_email="portcalls@agency.com",
                encrypted_credentials=encrypt_credentials({"password": "marketing-seed"}),
                imap_host="mail.agency.com",
                imap_port=993,
                imap_user="portcalls@agency.com",
                status="connected",
                last_sync_at=now - timedelta(minutes=45),
            ),
        ]
        for conn in integrations:
            db.add(conn)
        await db.flush()
        print("  Created 3 email integrations (Gmail, Outlook, IMAP)")
    else:
        for c in existing_conns:
            c.status = "connected"
            c.error_message = None
        await db.flush()
        print(f"  Reset {len(existing_conns)} integrations to connected (no error)")

    # Remove ALL emails for demo tenant (clean slate for marketing screenshots)
    await db.execute(delete(Email).where(Email.tenant_id == tenant_id))
    await db.flush()

    # Create sample emails - for Inbox / email list screenshots
    email_samples = [
        {
            "subject": "Port Call Notification - MSC Gulsun ETA Rotterdam 12-Mar",
            "sender": "port.ops@rotterdam.nl",
            "body": "Dear Agent,\n\nPlease find below the confirmed ETA for MSC Gulsun (IMO 9855811).\n\nETA: 12-Mar-2025 06:00 UTC\nBerth: CT-4\n\nBest regards,\nPort Operations",
        },
        {
            "subject": "Noon Report - Pacific Voyager - 08-Mar-2025",
            "sender": "master@pacific-voyager.com",
            "body": "Noon Report 08-Mar-2025\nPosition: 51.2N 003.5E\nDistance: 245 nm\nFuel consumed: 12.4 mt VLSFO\nETA Rotterdam: 10-Mar 14:00",
        },
        {
            "subject": "Disbursement Account Proforma - Ever Given - Shanghai",
            "sender": "accounts@shanghaiport.com",
            "body": "Please find attached proforma DA for port call Shanghai.\nTotal: USD 18,450.00\nValid until 15-Mar-2025.",
        },
        {
            "subject": "Bunker Delivery Note - Nordic Spirit - Singapore",
            "sender": "bunkers@singapore-fuel.com",
            "body": "BDN attached for Nordic Spirit.\nVLSFO: 85.2 mt\nMDO: 2.1 mt\nDelivery: 05-Mar-2025 08:00",
        },
        {
            "subject": "Port Call Update - HMM Oslo - Hamburg ETD revised",
            "sender": "hamburg.port@hpa.hamburg.de",
            "body": "ETD revised to 11-Mar-2025 18:00 due to cargo operations delay.",
        },
    ]
    for i, sample in enumerate(email_samples):
        pc = port_calls[i % len(port_calls)]
        external_id = f"marketing-email-{i + 1:03d}"
        received = now - timedelta(days=i + 1, hours=i * 2)
        em = Email(
            tenant_id=tenant_id,
            port_call_id=pc.id,
            external_id=external_id,
            subject=sample["subject"],
            sender=sample["sender"],
            body_text=sample["body"],
            processing_status="completed" if i < 3 else ("pending" if i == 3 else "processing"),
            received_at=received,
        )
        db.add(em)
        await db.flush()
        print(f"  Created {len(email_samples)} sample emails")

    await db.commit()
    print("Marketing seed completed successfully!")
    print("  Login: admin@shipflow.ai / admin123")
    print("  Screenshots: Vessels, Port Calls, DAs, Emissions, Emails, Settings > Integrations")


async def main() -> None:
    async with async_session_factory() as session:
        await seed_marketing(session)


if __name__ == "__main__":
    asyncio.run(main())
