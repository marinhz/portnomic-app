"""Email ingest: IMAP polling and webhook processing."""

import email as email_lib
import imaplib
import logging
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.email import Email
from app.models.parse_job import ParseJob
from app.redis_client import redis_client
from app.services.email_service import get_email_by_external_id
from app.services.limits import UPGRADE_MESSAGES, check_ai_parse_limit
from app.services.vessel_filter import get_tenant_vessel_terms, is_vessel_related_email

logger = logging.getLogger("shipflow.email_ingest")


async def ingest_and_enqueue(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    external_id: str,
    subject: str | None = None,
    sender: str | None = None,
    body_text: str | None = None,
    body_html: str | None = None,
    received_at: datetime | None = None,
    port_call_id: uuid.UUID | None = None,
) -> tuple[Email, ParseJob] | tuple[Email, None]:
    """Store email and create a parse job. Returns (email, job) or (email, None) if duplicate or over limit."""
    existing = await get_email_by_external_id(db, tenant_id, external_id)
    if existing:
        logger.info(
            "Duplicate email external_id=%s for tenant=%s, skipping", external_id, tenant_id
        )
        return existing, None

    result = await check_ai_parse_limit(db, tenant_id)
    if not result.allowed:
        logger.info(
            "AI parse limit exceeded for tenant=%s (%d/%s), skipping parse job",
            tenant_id,
            result.current,
            result.limit,
        )
        em = Email(
            tenant_id=tenant_id,
            external_id=external_id,
            subject=subject,
            sender=sender,
            body_text=body_text,
            body_html=body_html,
            received_at=received_at or datetime.now(timezone.utc),
            port_call_id=port_call_id,
            processing_status="limit_exceeded",
            error_reason=UPGRADE_MESSAGES.get("ai_parse", "Plan limit exceeded."),
        )
        db.add(em)
        await db.flush()
        await db.refresh(em)
        return em, None

    em = Email(
        tenant_id=tenant_id,
        external_id=external_id,
        subject=subject,
        sender=sender,
        body_text=body_text,
        body_html=body_html,
        received_at=received_at or datetime.now(timezone.utc),
        port_call_id=port_call_id,
        processing_status="pending",
    )
    db.add(em)
    await db.flush()
    await db.refresh(em)

    job = ParseJob(
        tenant_id=tenant_id,
        email_id=em.id,
        status="pending",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    return em, job


def _extract_body(msg: email_lib.message.Message) -> tuple[str | None, str | None]:
    """Extract text and html body from an email message."""
    body_text = None
    body_html = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" and body_text is None:
                payload = part.get_payload(decode=True)
                if payload:
                    body_text = payload.decode("utf-8", errors="replace")
            elif content_type == "text/html" and body_html is None:
                payload = part.get_payload(decode=True)
                if payload:
                    body_html = payload.decode("utf-8", errors="replace")
    else:
        content_type = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            decoded = payload.decode("utf-8", errors="replace")
            if content_type == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    return body_text, body_html


async def poll_imap(db: AsyncSession) -> int:
    """Poll IMAP mailbox for new emails. Returns count of newly ingested emails."""
    if not settings.imap_host:
        return 0

    tenant_id = (
        uuid.UUID(settings.imap_default_tenant_id) if settings.imap_default_tenant_id else None
    )
    if not tenant_id:
        logger.warning("IMAP_DEFAULT_TENANT_ID not set, skipping IMAP poll")
        return 0

    try:
        if settings.imap_use_ssl:
            mail = imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port)
        else:
            mail = imaplib.IMAP4(settings.imap_host, settings.imap_port)

        mail.login(settings.imap_user, settings.imap_password)
        mail.select("INBOX")

        _, data = mail.search(None, "UNSEEN")
        message_ids = data[0].split() if data[0] else []
        ingested = 0
        skipped_non_vessel = 0
        vessel_terms = (
            await get_tenant_vessel_terms(db, tenant_id) if settings.llm_vessel_only_sync else []
        )
        single_attempt = settings.llm_parse_single_attempt_on_ingest

        for msg_id in message_ids:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue

            raw_email = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw_email)

            external_id = msg.get("Message-ID", f"imap-{msg_id.decode()}")
            subject = msg.get("Subject")
            sender = msg.get("From")

            received_at = None
            date_str = msg.get("Date")
            if date_str:
                try:
                    received_at = parsedate_to_datetime(date_str)
                except Exception:
                    received_at = datetime.now(timezone.utc)

            body_text, body_html = _extract_body(msg)

            if settings.llm_vessel_only_sync and not is_vessel_related_email(
                subject, body_text, body_html, vessel_terms
            ):
                skipped_non_vessel += 1
                continue

            _, job = await ingest_and_enqueue(
                db,
                tenant_id,
                external_id=external_id,
                subject=subject,
                sender=sender,
                body_text=body_text,
                body_html=body_html,
                received_at=received_at,
            )
            if job:
                ingested += 1
                payload = f"{job.id}:{job.email_id}:{tenant_id}"
                if single_attempt:
                    payload += ":1"
                await redis_client.rpush("shipflow:parse_jobs", payload)

        mail.logout()
        logger.info(
            "IMAP poll: ingested %d, skipped %d non-vessel-related",
            ingested,
            skipped_non_vessel,
        )
        return ingested

    except Exception:
        logger.exception("IMAP poll failed")
        return 0
