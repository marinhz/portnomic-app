"""ARQ worker for background AI parse jobs.

Run with:  arq app.worker.WorkerSettings
"""

import asyncio
import logging
import uuid

from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.database import async_session_factory
from app.middleware.logging_middleware import setup_logging

setup_logging(settings.log_level)
from app.services.email_ingest import poll_imap
from app.services.llm_client import is_transient_error
from app.services.parse_worker import process_email

logger = logging.getLogger("shipflow.worker")


async def process_parse_job(ctx: dict, job_payload: str) -> None:
    """Process a single parse job from the queue.

    job_payload format: "{job_id}:{email_id}:{tenant_id}" or
    "{job_id}:{email_id}:{tenant_id}:1" for single attempt (no retries on ingest), or
    "{job_id}:{email_id}:{tenant_id}:emission" to force emission (Noon/Bunker) parsing.
    """
    parts = job_payload.split(":")
    if len(parts) not in (3, 4):
        logger.error("Invalid job payload: %s", job_payload)
        return

    job_id = uuid.UUID(parts[0])
    email_id = uuid.UUID(parts[1])
    single_attempt = len(parts) == 4 and parts[3] == "1"
    force_emission = len(parts) == 4 and parts[3] == "emission"

    max_retries = 0 if single_attempt else settings.llm_max_retries
    attempt = 0

    while attempt <= max_retries:
        async with async_session_factory() as db:
            try:
                await process_email(db, email_id, job_id, force_emission=force_emission)
                await db.commit()
                return
            except Exception as exc:
                await db.rollback()
                if is_transient_error(exc) and attempt < max_retries:
                    attempt += 1
                    wait = 2 ** attempt
                    logger.warning(
                        "Transient error on email %s (attempt %d/%d), retrying in %ds: %s",
                        email_id, attempt, max_retries, wait, exc,
                    )
                    await asyncio.sleep(wait)
                    continue

                logger.exception("Failed to process email %s after %d attempts", email_id, attempt)
                async with async_session_factory() as fail_db:
                    from app.services.email_service import update_email_status

                    await update_email_status(
                        fail_db,
                        email_id,
                        processing_status="failed",
                        error_reason=f"Max retries exceeded: {exc}",
                        increment_retry=True,
                    )
                    await fail_db.commit()
                return


async def poll_queue(ctx: dict) -> None:
    """Continuously poll Redis for parse jobs."""
    from app.redis_client import redis_client

    logger.info("Parse job queue poller started")
    while True:
        try:
            result = await redis_client.blpop("shipflow:parse_jobs", timeout=5)
            if result is None:
                continue
            _, payload = result
            await process_parse_job(ctx, payload)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error in queue poller")
            await asyncio.sleep(1)


async def imap_poll_task(ctx: dict) -> None:
    """Periodic IMAP polling for new emails (global + per-tenant connections)."""
    if settings.imap_host:
        async with async_session_factory() as db:
            try:
                count = await poll_imap(db)
                await db.commit()
                if count > 0:
                    logger.info("Global IMAP poll ingested %d emails", count)
            except Exception:
                await db.rollback()
                logger.exception("Global IMAP poll task failed")

    async with async_session_factory() as db:
        try:
            from app.services.oauth_ingest import poll_all_tenant_connections

            count = await poll_all_tenant_connections(db)
            await db.commit()
            if count > 0:
                logger.info("Per-tenant poll ingested %d emails", count)
        except Exception:
            await db.rollback()
            logger.exception("Per-tenant poll task failed")


async def startup(ctx: dict) -> None:
    logger.info("ARQ worker starting up")
    ctx["poll_task"] = asyncio.create_task(poll_queue(ctx))


async def shutdown(ctx: dict) -> None:
    logger.info("ARQ worker shutting down")
    poll_task = ctx.get("poll_task")
    if poll_task:
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            logger.info("Poll task cancelled cleanly")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    on_startup = startup
    on_shutdown = shutdown
    functions = [process_parse_job]
    cron_jobs = [
        cron(
            imap_poll_task,
            second={0},
            run_at_startup=True,
        ),
    ]
    max_jobs = 10
    job_timeout = 120
