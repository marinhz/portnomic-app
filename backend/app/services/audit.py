import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def _get_correlation_id() -> str | None:
    try:
        from app.middleware.logging_middleware import get_request_context

        ctx = get_request_context()
        return ctx.correlation_id or None
    except Exception:
        return None


async def log_action(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    payload: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    correlation_id: str | None = None,
) -> AuditLog:
    if correlation_id is None:
        correlation_id = _get_correlation_id()

    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id,
    )
    db.add(entry)
    await db.flush()
    return entry
