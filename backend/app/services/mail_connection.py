"""Mail connection service: CRUD, OAuth helpers, token encryption and refresh."""

import base64
import imaplib
import json
import logging
import socket
import ssl
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.mail_connection import MailConnection

logger = logging.getLogger("shipflow.mail_connection")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_SCOPES = "https://www.googleapis.com/auth/gmail.readonly openid email"

MICROSOFT_TOKEN_URL_TPL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
MICROSOFT_AUTH_URL_TPL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
MICROSOFT_SCOPES = "https://graph.microsoft.com/Mail.Read offline_access openid email"
MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"


# ── Encryption ────────────────────────────────────────────────────────────────


def _get_fernet() -> Fernet:
    passphrase = settings.oauth_state_encryption_key or settings.mfa_encryption_key
    raw = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"shipflow-mail-connection",
    ).derive(passphrase.encode())
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt_credentials(data: dict) -> str:
    return _get_fernet().encrypt(json.dumps(data).encode()).decode()


def decrypt_credentials(encrypted: str) -> dict:
    return json.loads(_get_fernet().decrypt(encrypted.encode()).decode())


def encrypt_state(data: dict) -> str:
    return _get_fernet().encrypt(json.dumps(data).encode()).decode()


def decrypt_state(token: str) -> dict:
    return json.loads(_get_fernet().decrypt(token.encode()).decode())


# ── OAuth URL builders ────────────────────────────────────────────────────────


def _redirect_uri() -> str:
    return f"{settings.oauth_redirect_base_url}/api/v1/integrations/email/callback"


def build_google_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def build_microsoft_auth_url(state: str) -> str:
    tenant = settings.microsoft_oauth_tenant or "common"
    auth_url = MICROSOFT_AUTH_URL_TPL.format(tenant=tenant)
    params = {
        "client_id": settings.microsoft_oauth_client_id,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": MICROSOFT_SCOPES,
        "state": state,
    }
    return f"{auth_url}?{urlencode(params)}"


# ── Token exchange ────────────────────────────────────────────────────────────


async def exchange_google_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": _redirect_uri(),
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_info = user_resp.json() if user_resp.is_success else {}

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "expires_at": _expires_at(tokens.get("expires_in", 3600)),
        "email": user_info.get("email"),
    }


async def exchange_microsoft_code(code: str) -> dict:
    tenant = settings.microsoft_oauth_tenant or "common"
    token_url = MICROSOFT_TOKEN_URL_TPL.format(tenant=tenant)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            data={
                "client_id": settings.microsoft_oauth_client_id,
                "client_secret": settings.microsoft_oauth_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": _redirect_uri(),
                "scope": MICROSOFT_SCOPES,
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

        user_resp = await client.get(
            MICROSOFT_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        user_info = user_resp.json() if user_resp.is_success else {}

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", ""),
        "expires_at": _expires_at(tokens.get("expires_in", 3600)),
        "email": user_info.get("mail") or user_info.get("userPrincipalName"),
    }


# ── Token refresh ─────────────────────────────────────────────────────────────


async def refresh_google_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", refresh_token),
        "expires_at": _expires_at(tokens.get("expires_in", 3600)),
    }


async def refresh_microsoft_token(refresh_token: str) -> dict:
    tenant = settings.microsoft_oauth_tenant or "common"
    token_url = MICROSOFT_TOKEN_URL_TPL.format(tenant=tenant)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            token_url,
            data={
                "client_id": settings.microsoft_oauth_client_id,
                "client_secret": settings.microsoft_oauth_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": MICROSOFT_SCOPES,
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", refresh_token),
        "expires_at": _expires_at(tokens.get("expires_in", 3600)),
    }


async def ensure_valid_token(conn: MailConnection) -> dict:
    """Decrypt credentials and refresh if expired. Returns plain credentials dict.

    Caller must persist updated encrypted_credentials if refresh occurred.
    """
    creds = decrypt_credentials(conn.encrypted_credentials)
    expires_at_str = creds.get("expires_at", "")
    if not expires_at_str:
        return creds

    expires_at = datetime.fromisoformat(expires_at_str)
    buffer = datetime.now(timezone.utc).timestamp() + 300  # 5 min buffer
    if expires_at.timestamp() > buffer:
        return creds

    refresh_tok = creds.get("refresh_token", "")
    if not refresh_tok:
        raise RuntimeError("No refresh_token available")

    try:
        if conn.provider == "gmail":
            new_tokens = await refresh_google_token(refresh_tok)
        elif conn.provider == "outlook":
            new_tokens = await refresh_microsoft_token(refresh_tok)
        else:
            return creds

        creds["access_token"] = new_tokens["access_token"]
        creds["refresh_token"] = new_tokens.get("refresh_token", refresh_tok)
        creds["expires_at"] = new_tokens["expires_at"]
        conn.encrypted_credentials = encrypt_credentials(creds)
        logger.info("Refreshed token for connection %s", conn.id)
        return creds
    except Exception:
        logger.exception("Token refresh failed for connection %s", conn.id)
        raise


def _expires_at(expires_in: int) -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=expires_in)
    return dt.isoformat()


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def list_connections(db: AsyncSession, tenant_id: uuid.UUID) -> list[MailConnection]:
    result = await db.execute(
        select(MailConnection)
        .where(MailConnection.tenant_id == tenant_id)
        .order_by(MailConnection.created_at.desc())
    )
    return list(result.scalars().all())


async def get_connection(
    db: AsyncSession, tenant_id: uuid.UUID, connection_id: uuid.UUID
) -> MailConnection | None:
    result = await db.execute(
        select(MailConnection).where(
            MailConnection.id == connection_id,
            MailConnection.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_connected_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> list[MailConnection]:
    result = await db.execute(
        select(MailConnection).where(
            MailConnection.tenant_id == tenant_id,
            MailConnection.status == "connected",
        )
    )
    return list(result.scalars().all())


async def get_all_connected(db: AsyncSession) -> list[MailConnection]:
    result = await db.execute(select(MailConnection).where(MailConnection.status == "connected"))
    return list(result.scalars().all())


async def upsert_oauth_connection(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    provider: str,
    token_data: dict,
) -> MailConnection:
    display_email = token_data.get("email")
    encrypted = encrypt_credentials(token_data)

    result = await db.execute(
        select(MailConnection).where(
            MailConnection.tenant_id == tenant_id,
            MailConnection.provider == provider,
            MailConnection.display_email == display_email,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.encrypted_credentials = encrypted
        existing.status = "connected"
        existing.error_message = None
        await db.flush()
        await db.refresh(existing)
        return existing

    conn = MailConnection(
        tenant_id=tenant_id,
        provider=provider,
        display_email=display_email,
        encrypted_credentials=encrypted,
        status="connected",
    )
    db.add(conn)
    await db.flush()
    await db.refresh(conn)
    return conn


# ── IMAP test (Task 6.12) ────────────────────────────────────────────────────


def _test_imap_sync(
    imap_host: str,
    imap_port: int,
    imap_user: str,
    imap_password: str,
) -> tuple[bool, str, str]:
    """Test IMAP connection and login. Returns (ok, error_code, message)."""
    try:
        mail = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=15)
        mail.login(imap_user, imap_password)
        mail.logout()
        return (True, "", "")
    except imaplib.IMAP4.error as e:
        msg = str(e).strip()
        if "AUTHENTICATIONFAILED" in msg.upper() or "LOGIN" in msg.upper():
            return (False, "auth_failed", "Authentication failed. Check username and password.")
        if "REFERRAL" in msg.upper():
            return (False, "invalid_host", "Invalid host or server configuration.")
        return (False, "imap_error", msg or "IMAP server error.")
    except ConnectionRefusedError:
        return (False, "connection_refused", "Connection refused. Check host, port, and firewall.")
    except socket.gaierror:
        return (False, "invalid_host", "Could not resolve host. Check hostname.")
    except (TimeoutError, socket.timeout):
        return (False, "timeout", "Connection timed out. Check host, port, and network.")
    except ssl.SSLError as e:
        return (False, "ssl_error", f"SSL error: {e}")
    except OSError as e:
        return (False, "connection_failed", str(e) or "Connection failed.")


async def test_imap_connection(
    imap_host: str,
    imap_port: int,
    imap_user: str,
    imap_password: str,
) -> tuple[bool, str, str]:
    """Async wrapper for IMAP test (runs sync imaplib in thread)."""
    import asyncio

    return await asyncio.to_thread(
        _test_imap_sync,
        imap_host,
        imap_port,
        imap_user,
        imap_password,
    )


def map_imap_exception_to_error(exc: BaseException) -> tuple[str, str]:
    """Map IMAP-related exceptions to (error_code, user_message)."""
    if isinstance(exc, imaplib.IMAP4.error):
        msg = str(exc).strip()
        if "AUTHENTICATIONFAILED" in msg.upper() or "LOGIN" in msg.upper():
            return ("auth_failed", "Authentication failed. Check username and password.")
        if "REFERRAL" in msg.upper():
            return ("invalid_host", "Invalid host or server configuration.")
        return ("imap_error", msg or "IMAP server error.")
    if isinstance(exc, ConnectionRefusedError):
        return ("connection_refused", "Connection refused. Check host, port, and firewall.")
    if isinstance(exc, socket.gaierror):
        return ("invalid_host", "Could not resolve host. Check hostname.")
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return ("timeout", "Connection timed out. Check host, port, and network.")
    if isinstance(exc, ssl.SSLError):
        return ("ssl_error", f"SSL error: {exc}")
    return ("connection_failed", str(exc) or "Connection failed.")


async def create_imap_connection(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    imap_host: str,
    imap_port: int,
    imap_user: str,
    imap_password: str,
) -> MailConnection:
    encrypted = encrypt_credentials({"password": imap_password})
    conn = MailConnection(
        tenant_id=tenant_id,
        provider="imap",
        display_email=f"{imap_user}@{imap_host}" if "@" not in imap_user else imap_user,
        imap_host=imap_host,
        imap_port=imap_port,
        imap_user=imap_user,
        encrypted_credentials=encrypted,
        status="connected",
    )
    db.add(conn)
    await db.flush()
    await db.refresh(conn)
    return conn


async def delete_connection(
    db: AsyncSession, tenant_id: uuid.UUID, connection_id: uuid.UUID
) -> bool:
    conn = await get_connection(db, tenant_id, connection_id)
    if conn is None:
        return False
    await db.delete(conn)
    await db.flush()
    return True


async def mark_connection_error(
    db: AsyncSession, connection_id: uuid.UUID, error_message: str
) -> None:
    result = await db.execute(select(MailConnection).where(MailConnection.id == connection_id))
    conn = result.scalar_one_or_none()
    if conn:
        conn.status = "error"
        conn.error_message = error_message
        await db.flush()


async def reset_sync_state_for_tenant(db: AsyncSession, tenant_id: uuid.UUID) -> int:
    """Clear last_sync_at and last_sync_cursor for all connected mailboxes. Returns count reset."""
    result = await db.execute(
        select(MailConnection).where(
            MailConnection.tenant_id == tenant_id,
            MailConnection.status == "connected",
        )
    )
    conns = list(result.scalars().all())
    for conn in conns:
        conn.last_sync_at = None
        conn.last_sync_cursor = None
    if conns:
        await db.flush()
    return len(conns)


async def update_sync_cursor(
    db: AsyncSession, connection_id: uuid.UUID, cursor: str | None
) -> None:
    result = await db.execute(select(MailConnection).where(MailConnection.id == connection_id))
    conn = result.scalar_one_or_none()
    if conn:
        conn.last_sync_at = datetime.now(timezone.utc)
        conn.last_sync_cursor = cursor
        await db.flush()
