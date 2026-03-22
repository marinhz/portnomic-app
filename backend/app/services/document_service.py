"""Document service for manual uploads."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentSourceType


async def find_document_by_content_hash(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    content_hash: str,
) -> Document | None:
    """Find an existing document with the given content hash (tenant-scoped).

    Used to prevent duplicate ingestion: same file content = same document,
    no re-parse, no redundant Sentinel audit.
    """
    result = await db.execute(
        select(Document)
        .where(
            Document.tenant_id == tenant_id,
            Document.content_hash == content_hash,
        )
        .order_by(Document.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_documents(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    port_call_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
    status_filter: str | None = None,
) -> tuple[list[Document], int]:
    """List documents for a port call (manual uploads only)."""
    base = select(Document).where(
        Document.tenant_id == tenant_id,
        Document.port_call_id == port_call_id,
        Document.source_type == DocumentSourceType.MANUAL_UPLOAD,
    )
    count_base = select(func.count()).select_from(Document).where(
        Document.tenant_id == tenant_id,
        Document.port_call_id == port_call_id,
        Document.source_type == DocumentSourceType.MANUAL_UPLOAD,
    )
    if status_filter:
        base = base.where(Document.processing_status == status_filter)
        count_base = count_base.where(Document.processing_status == status_filter)

    total = (await db.execute(count_base)).scalar_one()
    q = base.order_by(Document.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_document(
    db: AsyncSession, tenant_id: uuid.UUID, document_id: uuid.UUID
) -> Document | None:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def create_document(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    port_call_id: uuid.UUID,
    filename: str,
    body_text: str,
    category: str | None = None,
    content_hash: str | None = None,
) -> Document:
    doc = Document(
        tenant_id=tenant_id,
        port_call_id=port_call_id,
        source_type=DocumentSourceType.MANUAL_UPLOAD,
        filename=filename,
        category=category,
        content_hash=content_hash,
        body_text=body_text,
        processing_status="pending",
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def update_document_status(
    db: AsyncSession,
    document_id: uuid.UUID,
    *,
    processing_status: str | None = None,
    ai_raw_output: dict | None = None,
    error_reason: str | None = None,
    prompt_version: str | None = None,
    audit_status: str | None = None,
    increment_retry: bool = False,
) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        return None

    if processing_status is not None:
        doc.processing_status = processing_status
    if ai_raw_output is not None:
        doc.ai_raw_output = ai_raw_output
    if error_reason is not None:
        doc.error_reason = error_reason
    if prompt_version is not None:
        doc.prompt_version = prompt_version
    if audit_status is not None:
        doc.audit_status = audit_status
    if increment_retry:
        doc.retry_count += 1

    await db.flush()
    await db.refresh(doc)
    return doc
