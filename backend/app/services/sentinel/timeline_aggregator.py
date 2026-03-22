"""Timeline aggregator — fetches all sources, normalizes, returns unified TimelineEvent[] sorted by start.

Audit logic: Invoice (Manual/Email) vs SOF (Manual/Email) vs Noon Report (Manual/Email).
All three sources support both manual uploads (Document) and email ingestion (Email).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.disbursement_account import DisbursementAccount
from app.models.document import Document, DocumentSourceType
from app.models.emission_report import EmissionReport
from app.models.email import Email
from app.models.port_call import PortCall
from app.services.sentinel.ais_client import fetch_berth_data
from app.services.sentinel.ais_normalizer import normalize_ais
from app.services.sentinel.da_normalizer import normalize_da_line_items
from app.services.sentinel.models import TimelineEvent
from app.services.sentinel.noon_report_normalizer import normalize_noon_report
from app.services.sentinel.sof_normalizer import normalize_sof


async def get_timeline_events(
    db: AsyncSession,
    port_call_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> list[TimelineEvent]:
    """
    Fetches all sources for a port call, normalizes to TimelineEvent, returns merged sorted list.

    Sources (each from both Manual Upload and Email):
    - DA (Invoices): DisbursementAccount line_items (tug, pilot, berth)
    - SOF: Document/Email ai_raw_output with sof_timestamps or port_log
    - Noon Report: EmissionReport fuel_entries (from Document or Email)
    - AIS: Berth data from aisstream.io
    """
    events: list[TimelineEvent] = []

    # Load port call for eta/etd
    pc_result = await db.execute(
        select(PortCall)
        .where(PortCall.id == port_call_id, PortCall.tenant_id == tenant_id)
    )
    port_call = pc_result.scalar_one_or_none()
    if not port_call:
        return []

    # 1. DA normalizer — from DisbursementAccount (manual uploads + email)
    da_result = await db.execute(
        select(DisbursementAccount).where(
            DisbursementAccount.tenant_id == tenant_id,
            DisbursementAccount.port_call_id == port_call_id,
        )
    )
    for da in da_result.scalars().all():
        events.extend(
            normalize_da_line_items(
                line_items=da.line_items or [],
                source_document_id=da.id,
                port_call_id=port_call_id,
                eta=port_call.eta.isoformat() if port_call.eta else None,
                etd=port_call.etd.isoformat() if port_call.etd else None,
            )
        )

    # 2. SOF normalizer — from Email and Document ai_raw_output (sof_timestamps or port_log)
    for email in (
        await db.execute(
            select(Email).where(
                Email.tenant_id == tenant_id,
                Email.port_call_id == port_call_id,
            )
        )
    ).scalars().all():
        ai_raw = email.ai_raw_output or {}
        sof_data = ai_raw.get("sof_timestamps") or ai_raw.get("port_log")
        if sof_data and isinstance(sof_data, dict):
            events.extend(
                normalize_sof(
                    sof_data=sof_data,
                    source_document_id=email.id,
                    port_call_id=port_call_id,
                )
            )

    doc_result = await db.execute(
        select(Document).where(
            Document.tenant_id == tenant_id,
            Document.port_call_id == port_call_id,
            Document.source_type == DocumentSourceType.MANUAL_UPLOAD,
            Document.processing_status == "completed",
        )
    )
    for doc in doc_result.scalars().all():
        ai_raw = doc.ai_raw_output or {}
        sof_data = ai_raw.get("sof_timestamps") or ai_raw.get("port_log")
        if sof_data and isinstance(sof_data, dict):
            events.extend(
                normalize_sof(
                    sof_data=sof_data,
                    source_document_id=doc.id,
                    port_call_id=port_call_id,
                )
            )

    # 3. Noon Report normalizer — from EmissionReport (manual + email; report_date + fuel_entries)
    er_result = await db.execute(
        select(EmissionReport)
        .where(
            EmissionReport.tenant_id == tenant_id,
            EmissionReport.port_call_id == port_call_id,
        )
        .options(selectinload(EmissionReport.fuel_entries))
    )
    for report in er_result.scalars().all():
        fuel_dicts = [
            {
                "fuel_type": e.fuel_type,
                "consumption_mt": float(e.consumption_mt),
                "operational_status": e.operational_status,
            }
            for e in report.fuel_entries
        ]
        events.extend(
            normalize_noon_report(
                report_id=report.id,
                port_call_id=port_call_id,
                report_date=report.report_date,
                fuel_entries=fuel_dicts,
                distance_nm=float(report.distance_nm) if report.distance_nm else None,
                email_id=report.email_id,
            )
        )

    # 4. AIS normalizer — fetches berth data from aisstream.io; graceful degradation if unavailable
    berth_data = await fetch_berth_data(db, port_call_id, tenant_id)
    events.extend(normalize_ais(berth_data=berth_data, port_call_id=port_call_id))

    # Sort by start
    events.sort(key=lambda e: e.start)
    return events
