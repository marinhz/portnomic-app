import hashlib
import hmac
import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.database import get_db
from app.redis_client import redis_client
from app.services.email_ingest import ingest_and_enqueue
from app.services.vessel_filter import get_tenant_vessel_terms, is_vessel_related_email

logger = logging.getLogger("shipflow.webhooks")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _resolve_tenant_from_recipient(to_address: str) -> uuid.UUID | None:
    """Resolve tenant from the destination email address.

    Convention: inbound+<tenant_slug>@shipflow.ai
    Falls back to default tenant for development.
    """
    _ = to_address  # reserved for future slug-based tenant resolution
    if settings.imap_default_tenant_id:
        return uuid.UUID(settings.imap_default_tenant_id)
    return None


def _verify_signature(payload: bytes, signature: str | None) -> bool:
    """Verify webhook signature. In production, secret is required."""
    if not settings.webhook_inbound_secret:
        if settings.environment == "production":
            return False
        return True
    if not signature:
        return False
    expected = hmac.new(
        settings.webhook_inbound_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/inbound-email", status_code=status.HTTP_200_OK)
async def inbound_email_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str | None = Header(default=None),
) -> dict:
    """Receive inbound emails via webhook (e.g. SendGrid Inbound Parse)."""
    body = await request.body()

    if not _verify_signature(body, x_webhook_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    to_address = data.get("to", "")
    tenant_id = _resolve_tenant_from_recipient(to_address)
    if not tenant_id:
        logger.warning("Could not resolve tenant for recipient: %s", to_address)
        return {"status": "skipped", "reason": "unknown_tenant"}

    external_id = data.get("message_id") or data.get("Message-ID") or str(uuid.uuid4())
    subject = data.get("subject")
    sender = data.get("from") or data.get("from_email")
    body_text = data.get("text")
    body_html = data.get("html")

    if settings.llm_vessel_only_sync:
        vessel_terms = await get_tenant_vessel_terms(db, tenant_id)
        if not is_vessel_related_email(subject, body_text, body_html, vessel_terms):
            logger.info("Webhook: skipped non-vessel-related email for tenant %s", tenant_id)
            return {"status": "skipped", "reason": "non_vessel_related"}

    em, job = await ingest_and_enqueue(
        db,
        tenant_id,
        external_id=external_id,
        subject=subject,
        sender=sender,
        body_text=body_text,
        body_html=body_html,
    )

    if job:
        payload = f"{job.id}:{em.id}:{tenant_id}"
        if settings.llm_parse_single_attempt_on_ingest:
            payload += ":1"
        await redis_client.rpush("shipflow:parse_jobs", payload)
        logger.info("Webhook: ingested email %s, job %s", em.id, job.id)
        return {"status": "queued", "email_id": str(em.id), "job_id": str(job.id)}

    return {"status": "duplicate", "email_id": str(em.id)}
