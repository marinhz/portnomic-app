"""Discrepancy service for Sentinel Operational Gap Engine."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.disbursement_account import DisbursementAccount
from app.models.discrepancy import Discrepancy
from app.models.document import Document, DocumentSourceType
from app.models.email import Email
from app.models.emission_report import EmissionReport


async def resolve_source_labels(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    source_document_ids: list[uuid.UUID],
) -> dict[uuid.UUID, str]:
    """Resolve source document IDs to human-readable labels for UI display.

    Maps each UUID to a label such as:
    - Document (manual): "Manual PDF: filename.pdf"
    - Email: "Email from sender@example.com" or "Email: Subject..."
    - DisbursementAccount: "Invoice"
    - EmissionReport: "Noon Report (manual)" or "Noon Report (email)"
    """
    if not source_document_ids:
        return {}

    ids_set = set(source_document_ids)
    labels: dict[uuid.UUID, str] = {}

    # Documents (manual uploads)
    doc_result = await db.execute(
        select(Document.id, Document.filename).where(
            Document.tenant_id == tenant_id,
            Document.id.in_(ids_set),
            Document.source_type == DocumentSourceType.MANUAL_UPLOAD,
        )
    )
    for row in doc_result.all():
        labels[row.id] = f"Manual PDF: {row.filename or 'document'}"
        ids_set.discard(row.id)

    # Emails
    email_result = await db.execute(
        select(Email.id, Email.sender, Email.subject).where(
            Email.tenant_id == tenant_id,
            Email.id.in_(ids_set),
        )
    )
    for row in email_result.all():
        if row.sender:
            labels[row.id] = f"Email from {row.sender}"
        else:
            subj = (row.subject or "Unknown")[:50]
            labels[row.id] = f"Email: {subj}{'…' if len(row.subject or '') > 50 else ''}"
        ids_set.discard(row.id)

    # DisbursementAccounts (Invoice/DA)
    da_result = await db.execute(
        select(DisbursementAccount.id).where(
            DisbursementAccount.tenant_id == tenant_id,
            DisbursementAccount.id.in_(ids_set),
        )
    )
    for row in da_result.all():
        labels[row.id] = "Invoice"
        ids_set.discard(row.id)

    # EmissionReports (Noon Report — check if from manual or email)
    er_result = await db.execute(
        select(EmissionReport.id, EmissionReport.document_id, EmissionReport.email_id).where(
            EmissionReport.tenant_id == tenant_id,
            EmissionReport.id.in_(ids_set),
        )
    )
    for row in er_result.all():
        labels[row.id] = (
            "Noon Report (manual)" if row.document_id else "Noon Report (email)"
        )
        ids_set.discard(row.id)

    # Any unresolved IDs
    for uid in ids_set:
        labels[uid] = "Unknown source"

    return labels


async def list_discrepancies_for_port_call(
    db: AsyncSession, tenant_id: uuid.UUID, port_call_id: uuid.UUID
) -> list[Discrepancy]:
    """List discrepancies for a port call, tenant-scoped."""
    result = await db.execute(
        select(Discrepancy)
        .where(
            Discrepancy.port_call_id == port_call_id,
            Discrepancy.tenant_id == tenant_id,
        )
        .order_by(Discrepancy.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_discrepancies_for_port_call(
    db: AsyncSession, tenant_id: uuid.UUID, port_call_id: uuid.UUID
) -> int:
    """Delete all discrepancies for a port call. Returns number of rows deleted."""
    result = await db.execute(
        delete(Discrepancy).where(
            Discrepancy.port_call_id == port_call_id,
            Discrepancy.tenant_id == tenant_id,
        )
    )
    return result.rowcount or 0
