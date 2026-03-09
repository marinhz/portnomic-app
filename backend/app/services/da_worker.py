"""Background worker tasks for DA PDF generation and email dispatch."""

import logging
import uuid

from app.database import async_session_factory
from app.services.disbursement_account import get_da, mark_sent
from app.services.email_dispatch import send_da_email
from app.services.pdf_generator import generate_pdf
from app.services.storage import store_blob

logger = logging.getLogger("shipflow.da_worker")


async def process_da_send(
    tenant_id: uuid.UUID,
    da_id: uuid.UUID,
    to_addresses: list[str] | None = None,
) -> bool:
    """Generate PDF, store it, send email, and mark DA as sent.

    Returns True on success, False on failure.
    """
    async with async_session_factory() as db:
        try:
            da = await get_da(db, tenant_id, da_id)
            if da is None:
                logger.error("DA %s not found for tenant %s", da_id, tenant_id)
                return False

            if da.status != "approved":
                logger.error("DA %s is not approved (status=%s)", da_id, da.status)
                return False

            da_data = {
                "id": str(da.id),
                "type": da.type,
                "version": da.version,
                "status": da.status,
                "currency": da.currency,
                "line_items": da.line_items,
                "totals": da.totals,
            }

            pdf_bytes = await generate_pdf(da_data)

            blob_id = await store_blob(pdf_bytes, "pdf")
            da.pdf_blob_id = blob_id
            await db.flush()

            if to_addresses:
                sent = await send_da_email(to_addresses, da_data, pdf_bytes)
                if not sent:
                    logger.warning("Email dispatch failed for DA %s; PDF saved but not emailed", da_id)

            await mark_sent(db, da_id)
            await db.commit()

            logger.info("DA %s processed: PDF stored (%s), marked sent", da_id, blob_id)
            return True
        except Exception:
            await db.rollback()
            logger.exception("Failed to process DA send for %s", da_id)
            return False
