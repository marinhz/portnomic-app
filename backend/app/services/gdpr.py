import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.disbursement_account import DisbursementAccount
from app.models.email import Email
from app.models.port_call import PortCall
from app.models.tenant import Tenant
from app.models.user import User
from app.models.vessel import Vessel
from app.schemas.gdpr import ProcessingRecordEntry, RetentionPolicyConfig
from app.services import audit as audit_svc

PROCESSING_RECORDS: list[dict] = [
    {
        "activity": "Port Call Management",
        "data_categories": ["vessel data", "port data", "scheduling"],
        "purpose": "Operational management of vessel port calls",
        "retention": "7 years (regulatory)",
        "safeguards": "Encryption at rest, tenant isolation, RBAC",
    },
    {
        "activity": "Disbursement Account Processing",
        "data_categories": ["financial data", "vessel data", "port charges"],
        "purpose": "Calculation and management of port disbursement accounts",
        "retention": "7 years (financial regulation)",
        "safeguards": "Encryption at rest, audit logging, approval workflows",
    },
    {
        "activity": "Email Ingestion & AI Parsing",
        "data_categories": ["email content", "sender information", "attachments"],
        "purpose": "Automated extraction of port call and tariff data from emails",
        "retention": "1 year",
        "safeguards": "Encryption in transit/at rest, access controls, data minimization",
    },
    {
        "activity": "User Account Management",
        "data_categories": ["email address", "authentication credentials", "role assignments"],
        "purpose": "Authentication, authorization, and user administration",
        "retention": "Duration of account + 90 days after deletion",
        "safeguards": "Password hashing, MFA, JWT tokens, RBAC",
    },
    {
        "activity": "Audit Logging",
        "data_categories": ["user actions", "IP addresses", "user agents"],
        "purpose": "Security monitoring, compliance, and forensic analysis",
        "retention": "7 years",
        "safeguards": "Append-only storage, tenant isolation, encryption at rest",
    },
]


def _serialize_row(row, exclude: set[str] | None = None) -> dict:
    exclude = exclude or set()
    result = {}
    for col in row.__table__.columns:
        if col.name in exclude:
            continue
        val = getattr(row, col.name)
        if isinstance(val, (datetime,)):
            val = val.isoformat()
        elif isinstance(val, uuid.UUID):
            val = str(val)
        result[col.name] = val
    return result


async def export_user_data(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    format: str = "json",
) -> dict:
    user_result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        return {"error": "user_not_found"}

    profile = _serialize_row(user, exclude={"password_hash", "mfa_secret"})

    vessels_result = await db.execute(
        select(Vessel).where(Vessel.tenant_id == tenant_id)
    )
    vessels = [_serialize_row(v) for v in vessels_result.scalars().all()]

    port_calls_result = await db.execute(
        select(PortCall).where(PortCall.tenant_id == tenant_id)
    )
    port_calls = [_serialize_row(pc) for pc in port_calls_result.scalars().all()]

    das_result = await db.execute(
        select(DisbursementAccount).where(DisbursementAccount.tenant_id == tenant_id)
    )
    disbursement_accounts = [_serialize_row(da) for da in das_result.scalars().all()]

    emails_result = await db.execute(
        select(Email).where(Email.tenant_id == tenant_id)
    )
    emails = [_serialize_row(e) for e in emails_result.scalars().all()]

    export = {
        "user_profile": profile,
        "vessels": vessels,
        "port_calls": port_calls,
        "disbursement_accounts": disbursement_accounts,
        "emails": emails,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    if format == "csv":
        flat: dict[str, list[dict]] = {}
        flat["user_profile"] = [profile]
        flat["vessels"] = vessels
        flat["port_calls"] = port_calls
        flat["disbursement_accounts"] = disbursement_accounts
        flat["emails"] = emails
        return {"format": "csv", "tables": flat}

    return export


async def erase_user(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
) -> dict:
    user_result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        return {"error": "user_not_found"}

    anonymized_email = f"deleted-{uuid.uuid4()}@anonymized.local"
    original_email = user.email

    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    user.email = anonymized_email
    user.mfa_secret = None
    user.mfa_enabled = False
    user.password_hash = "REDACTED"

    anonymized_fields = ["email", "password_hash", "mfa_secret", "mfa_enabled", "is_active"]
    retained_for_legal = ["audit_logs", "disbursement_accounts", "port_calls"]

    user_id_hash = hashlib.sha256(str(user_id).encode()).hexdigest()[:16]
    await db.execute(
        update(AuditLog)
        .where(AuditLog.user_id == user_id, AuditLog.tenant_id == tenant_id)
        .values(user_id=None, payload=AuditLog.payload.concat({"anonymized_user": user_id_hash}))
    )

    await audit_svc.log_action(
        db,
        tenant_id=tenant_id,
        user_id=requesting_user_id,
        action="gdpr_erasure",
        resource_type="user",
        resource_id=str(user_id),
        payload={
            "original_email_domain": original_email.split("@")[-1],
            "anonymized_fields": anonymized_fields,
            "retained_for_legal": retained_for_legal,
        },
    )

    await db.flush()

    return {
        "user_id": user_id,
        "status": "erased",
        "anonymized_fields": anonymized_fields,
        "retained_for_legal": retained_for_legal,
        "processed_at": datetime.now(timezone.utc),
    }


async def get_retention_policy(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict:
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return {"error": "tenant_not_found"}

    settings = tenant.settings or {}
    policy_data = settings.get("retention_policy", {})
    config = RetentionPolicyConfig(**policy_data)

    return {
        "tenant_id": tenant_id,
        "config": config.model_dump(),
        "updated_at": settings.get("retention_policy_updated_at"),
    }


async def update_retention_policy(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    config: dict,
) -> dict:
    result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        return {"error": "tenant_not_found"}

    settings = tenant.settings or {}
    settings["retention_policy"] = config
    settings["retention_policy_updated_at"] = datetime.now(timezone.utc).isoformat()
    tenant.settings = settings

    await db.flush()

    return {
        "tenant_id": tenant_id,
        "config": config,
        "updated_at": settings["retention_policy_updated_at"],
    }


async def run_retention_purge(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict:
    policy_result = await get_retention_policy(db, tenant_id)
    if "error" in policy_result:
        return policy_result

    config = RetentionPolicyConfig(**policy_result["config"])
    now = datetime.now(timezone.utc)
    counts: dict[str, int] = {}

    # Hard-delete soft-deleted users past purge window
    purge_cutoff = now - timedelta(days=config.purge_soft_deleted_after_days)
    purge_result = await db.execute(
        select(User).where(
            User.tenant_id == tenant_id,
            User.is_active.is_(False),
            User.deleted_at.isnot(None),
            User.deleted_at < purge_cutoff,
        )
    )
    users_to_purge = purge_result.scalars().all()
    for user in users_to_purge:
        await db.delete(user)
    counts["users_hard_deleted"] = len(users_to_purge)

    # Soft-delete emails past retention window
    email_cutoff = now - timedelta(days=config.email_retention_days)
    email_result = await db.execute(
        select(Email).where(
            Email.tenant_id == tenant_id,
            Email.created_at < email_cutoff,
        )
    )
    emails_to_purge = email_result.scalars().all()
    for email in emails_to_purge:
        email.processing_status = "purged"
        email.body_text = None
        email.body_html = None
        email.ai_raw_output = None
    counts["emails_purged"] = len(emails_to_purge)

    # Audit logs are never purged before audit_log_retention_days
    audit_cutoff = now - timedelta(days=config.audit_log_retention_days)
    audit_result = await db.execute(
        select(AuditLog).where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at < audit_cutoff,
        )
    )
    audit_logs_to_purge = audit_result.scalars().all()
    for log in audit_logs_to_purge:
        await db.delete(log)
    counts["audit_logs_deleted"] = len(audit_logs_to_purge)

    await db.flush()

    return {
        "tenant_id": tenant_id,
        "purged_at": now.isoformat(),
        "counts": counts,
    }


def get_processing_records() -> list[ProcessingRecordEntry]:
    return [ProcessingRecordEntry(**entry) for entry in PROCESSING_RECORDS]
