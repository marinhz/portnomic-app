"""Ingest emails from OAuth-connected mailboxes (Gmail API, Microsoft Graph) and per-tenant IMAP."""

import email as email_lib
import imaplib
import logging
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.mail_connection import MailConnection

# Demo tenant (seed data) uses placeholder credentials; skip sync to avoid marking as error
DEMO_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
from app.redis_client import redis_client
from app.services.email_ingest import _extract_body, ingest_and_enqueue
from app.services.mail_connection import (
    decrypt_credentials,
    ensure_valid_token,
    get_all_connected,
    get_connected_for_tenant,
    mark_connection_error,
    update_sync_cursor,
)
from app.utils.email_headers import decode_mime_header
from app.services.vessel_filter import get_tenant_vessel_terms, is_vessel_related_email

logger = logging.getLogger("shipflow.oauth_ingest")

GMAIL_MESSAGES_URL = "https://www.googleapis.com/gmail/v1/users/me/messages"
GMAIL_MESSAGE_URL = "https://www.googleapis.com/gmail/v1/users/me/messages/{id}"
GRAPH_MESSAGES_URL = "https://graph.microsoft.com/v1.0/me/messages"


async def poll_all_tenant_connections(db: AsyncSession) -> int:
    """Fetch new emails from all connected per-tenant mailboxes. Returns total ingested."""
    connections = await get_all_connected(db)
    connections = [c for c in connections if c.tenant_id != DEMO_TENANT_ID]
    logger.info(
        "Per-tenant poll: %d connected mailbox(es) %s",
        len(connections),
        [f"{c.provider}:{c.display_email}" for c in connections] if connections else [],
    )
    total = 0

    for conn in connections:
        try:
            if conn.provider == "gmail":
                count = await _poll_gmail(db, conn)
            elif conn.provider == "outlook":
                count = await _poll_outlook(db, conn)
            elif conn.provider == "imap":
                count = await _poll_tenant_imap(db, conn)
            else:
                continue
            total += count
        except Exception as exc:
            logger.exception(
                "Failed to poll connection %s (provider=%s, tenant=%s)",
                conn.id,
                conn.provider,
                conn.tenant_id,
            )
            await mark_connection_error(db, conn.id, str(exc)[:500])

    return total


async def poll_tenant_connections(
    db: AsyncSession, tenant_id: uuid.UUID, *, full: bool = False
) -> int:
    """Fetch new emails from this tenant's connected mailboxes. Returns total ingested."""
    if tenant_id == DEMO_TENANT_ID:
        return 0
    connections = await get_connected_for_tenant(db, tenant_id)
    logger.info(
        "Sync: tenant=%s has %d connected mailbox(es): %s (full=%s)",
        tenant_id,
        len(connections),
        [f"{c.provider}:{c.display_email}" for c in connections],
        full,
    )
    total = 0
    for conn in connections:
        try:
            if conn.provider == "gmail":
                count = await _poll_gmail(db, conn)
            elif conn.provider == "outlook":
                count = await _poll_outlook(db, conn)
            elif conn.provider == "imap":
                count = await _poll_tenant_imap(db, conn, full=full)
            else:
                continue
            total += count
        except Exception as exc:
            logger.exception(
                "Failed to poll connection %s (provider=%s, tenant=%s)",
                conn.id,
                conn.provider,
                conn.tenant_id,
            )
            await mark_connection_error(db, conn.id, str(exc)[:500])
    return total


async def _poll_gmail(db: AsyncSession, conn: MailConnection) -> int:
    creds = await ensure_valid_token(conn)
    await db.flush()

    access_token = creds.get("access_token") or ""
    if not access_token.strip():
        raise RuntimeError(
            "Gmail connection has no valid access token. "
            "Disconnect and reconnect Gmail in Settings → Integrations to re-authorize."
        )
    headers = {"Authorization": f"Bearer {access_token}"}

    params: dict = {"maxResults": 50}

    # pageToken is only valid for the exact query that produced it. When we have
    # last_sync_at we use after: in q, which changes the query — so we must NOT
    # use pageToken (it was from a different query). Using both causes empty/wrong results.
    use_incremental = conn.last_sync_at is not None
    if use_incremental:
        # Gmail only accepts YYYY/MM/DD for after: — Unix timestamps are not supported
        after_date = conn.last_sync_at.strftime("%Y/%m/%d")
        params["q"] = f"in:inbox after:{after_date}"
    else:
        # Full sync: use labelIds for INBOX — more reliable than q=in:inbox per Gmail API
        if conn.last_sync_cursor:
            params["pageToken"] = conn.last_sync_cursor
        params["labelIds"] = ["INBOX"]

    ingested = 0
    skipped_duplicates = 0
    skipped_non_vessel = 0
    vessel_terms = (
        await get_tenant_vessel_terms(db, conn.tenant_id) if settings.llm_vessel_only_sync else []
    )
    single_attempt = settings.llm_parse_single_attempt_on_ingest

    async with httpx.AsyncClient() as client:
        resp = await client.get(GMAIL_MESSAGES_URL, headers=headers, params=params)
        if not resp.is_success:
            err_msg = f"Gmail API {resp.status_code}"
            try:
                err_body = resp.json()
                err_msg = err_body.get("error", {}).get("message", resp.text[:200])
                logger.error("Gmail API error %d: %s", resp.status_code, err_msg)
            except Exception:
                logger.exception("Gmail API request failed: %s", resp.text[:500])
            raise RuntimeError(f"Gmail API {resp.status_code}: {err_msg}") from None
        data = resp.json()

        messages = data.get("messages", [])
        logger.info(
            "Gmail list: tenant=%s q=%r labelIds=%r returned %d message(s)",
            conn.tenant_id,
            params.get("q"),
            params.get("labelIds"),
            len(messages),
        )
        next_page = data.get("nextPageToken")

        for msg_stub in messages:
            msg_resp = await client.get(
                GMAIL_MESSAGE_URL.format(id=msg_stub["id"]),
                headers=headers,
                params={"format": "full"},
            )
            if not msg_resp.is_success:
                continue

            msg_data = msg_resp.json()
            email_data = _parse_gmail_message(msg_data)

            if settings.llm_vessel_only_sync and not is_vessel_related_email(
                email_data.get("subject"),
                email_data.get("body_text"),
                email_data.get("body_html"),
                vessel_terms,
            ):
                skipped_non_vessel += 1
                continue

            _, job = await ingest_and_enqueue(
                db,
                conn.tenant_id,
                external_id=f"gmail-{msg_stub['id']}",
                subject=email_data.get("subject"),
                sender=email_data.get("sender"),
                body_text=email_data.get("body_text"),
                body_html=email_data.get("body_html"),
                received_at=email_data.get("received_at"),
            )
            if job:
                ingested += 1
                payload = f"{job.id}:{job.email_id}:{conn.tenant_id}"
                if single_attempt:
                    payload += ":1"
                await redis_client.rpush("shipflow:parse_jobs", payload)
            else:
                skipped_duplicates += 1

    # For incremental sync, do not persist pageToken — it was for a different query
    cursor_to_save = None if use_incremental else next_page
    await update_sync_cursor(db, conn.id, cursor_to_save)
    logger.info(
        "Gmail: tenant=%s ingested %d, skipped %d duplicate(s), %d non-vessel-related",
        conn.tenant_id,
        ingested,
        skipped_duplicates,
        skipped_non_vessel,
    )
    return ingested


def _parse_gmail_message(msg: dict) -> dict:
    headers_list = msg.get("payload", {}).get("headers", [])
    headers_map = {h["name"].lower(): h["value"] for h in headers_list}

    received_at = None
    date_str = headers_map.get("date")
    if date_str:
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = datetime.now(timezone.utc)

    body_text = None
    body_html = None
    payload = msg.get("payload", {})
    parts = payload.get("parts", [])

    if parts:
        for part in parts:
            mime_type = part.get("mimeType", "")
            body_data = part.get("body", {}).get("data", "")
            if body_data:
                import base64

                decoded = base64.urlsafe_b64decode(body_data + "==").decode(
                    "utf-8", errors="replace"
                )
                if mime_type == "text/plain" and not body_text:
                    body_text = decoded
                elif mime_type == "text/html" and not body_html:
                    body_html = decoded
    else:
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            import base64

            decoded = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
            if payload.get("mimeType") == "text/html":
                body_html = decoded
            else:
                body_text = decoded

    return {
        "subject": decode_mime_header(headers_map.get("subject")),
        "sender": decode_mime_header(headers_map.get("from")),
        "body_text": body_text,
        "body_html": body_html,
        "received_at": received_at,
    }


async def _poll_outlook(db: AsyncSession, conn: MailConnection) -> int:
    creds = await ensure_valid_token(conn)
    await db.flush()

    access_token = creds["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    params: dict = {
        "$top": 50,
        "$orderby": "receivedDateTime desc",
        "$select": "id,subject,from,body,receivedDateTime,isRead",
    }

    if conn.last_sync_at:
        filter_dt = conn.last_sync_at.strftime("%Y-%m-%dT%H:%M:%SZ")
        params["$filter"] = f"receivedDateTime ge {filter_dt}"

    ingested = 0
    skipped_non_vessel = 0
    vessel_terms = (
        await get_tenant_vessel_terms(db, conn.tenant_id) if settings.llm_vessel_only_sync else []
    )
    single_attempt = settings.llm_parse_single_attempt_on_ingest

    async with httpx.AsyncClient() as client:
        resp = await client.get(GRAPH_MESSAGES_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        for msg in data.get("value", []):
            body = msg.get("body", {})
            body_text = body.get("content") if body.get("contentType") == "text" else None
            body_html = body.get("content") if body.get("contentType") == "html" else None

            received_at = None
            if msg.get("receivedDateTime"):
                try:
                    received_at = datetime.fromisoformat(
                        msg["receivedDateTime"].replace("Z", "+00:00")
                    )
                except Exception:
                    received_at = datetime.now(timezone.utc)

            sender = None
            from_field = msg.get("from", {}).get("emailAddress", {})
            if from_field:
                raw = from_field.get("address") or from_field.get("name")
                sender = decode_mime_header(raw) if isinstance(raw, str) else raw

            subject = decode_mime_header(msg.get("subject"))
            if settings.llm_vessel_only_sync and not is_vessel_related_email(
                subject, body_text, body_html, vessel_terms
            ):
                skipped_non_vessel += 1
                continue

            _, job = await ingest_and_enqueue(
                db,
                conn.tenant_id,
                external_id=f"outlook-{msg['id']}",
                subject=subject,
                sender=sender,
                body_text=body_text,
                body_html=body_html,
                received_at=received_at,
            )
            if job:
                ingested += 1
                payload = f"{job.id}:{job.email_id}:{conn.tenant_id}"
                if single_attempt:
                    payload += ":1"
                await redis_client.rpush("shipflow:parse_jobs", payload)

    await update_sync_cursor(db, conn.id, None)
    logger.info(
        "Outlook: tenant=%s ingested %d, skipped %d non-vessel-related",
        conn.tenant_id,
        ingested,
        skipped_non_vessel,
    )
    return ingested


async def _poll_tenant_imap(db: AsyncSession, conn: MailConnection, *, full: bool = False) -> int:
    creds = decrypt_credentials(conn.encrypted_credentials)
    password = creds.get("password", "")
    if not conn.imap_host or not conn.imap_user or not password:
        logger.warning("IMAP connection %s missing host/user/password", conn.id)
        return 0

    try:
        imap_port = conn.imap_port or 993
        mail = imaplib.IMAP4_SSL(conn.imap_host, imap_port)
        mail.login(conn.imap_user, password)
        mail.select("INBOX")

        # Full sync: fetch ALL emails (including read). Normal sync: only UNSEEN (unread).
        search_criterion = "ALL" if full else "UNSEEN"

        # Try UID SEARCH first (stable IDs); fall back to SEARCH on any UID error (cPanel/Dovecot compatibility).
        use_uid = True
        try:
            _, data = mail.uid("SEARCH", None, search_criterion)
            ids = data[0].split() if data[0] else []
        except imaplib.IMAP4.error as e:
            logger.info(
                "IMAP UID SEARCH failed, falling back to SEARCH: %s",
                e,
            )
            use_uid = False
            _, data = mail.search(None, search_criterion)
            ids = data[0].split() if data[0] else []

        ingested = 0
        skipped_non_vessel = 0
        vessel_terms = (
            await get_tenant_vessel_terms(db, conn.tenant_id)
            if settings.llm_vessel_only_sync
            else []
        )
        single_attempt = settings.llm_parse_single_attempt_on_ingest

        for msg_id in ids:
            if use_uid:
                _, msg_data = mail.uid("FETCH", msg_id, "(RFC822)")
            else:
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue

            raw_email = msg_data[0][1]
            if raw_email is None:
                continue
            msg = email_lib.message_from_bytes(raw_email)

            # Prefer Message-ID; fallback: UID if available (stable), else sequence (can change).
            mid = msg.get("Message-ID")
            if mid:
                external_id = str(mid).strip()
            elif use_uid:
                uid_str = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
                external_id = f"imap-uid-{conn.id}-{uid_str}"
            else:
                mid_str = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
                external_id = f"imap-{conn.id}-{mid_str}"
            subject = decode_mime_header(msg.get("Subject"))
            sender = decode_mime_header(msg.get("From"))

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
                conn.tenant_id,
                external_id=external_id,
                subject=subject,
                sender=sender,
                body_text=body_text,
                body_html=body_html,
                received_at=received_at,
            )
            if job:
                ingested += 1
                payload = f"{job.id}:{job.email_id}:{conn.tenant_id}"
                if single_attempt:
                    payload += ":1"
                await redis_client.rpush("shipflow:parse_jobs", payload)

        mail.logout()
        await update_sync_cursor(db, conn.id, None)
        skipped_other = len(ids) - ingested - skipped_non_vessel
        logger.info(
            "Tenant IMAP: tenant=%s fetched %d, ingested %d, skipped %d non-vessel, %d duplicate/limit",
            conn.tenant_id,
            len(ids),
            ingested,
            skipped_non_vessel,
            skipped_other,
        )
        return ingested

    except Exception:
        logger.exception("Tenant IMAP poll failed for connection %s", conn.id)
        raise
