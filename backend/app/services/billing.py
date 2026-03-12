"""Billing service — myPOS Web Checkout, notify processing.

Task 8.6: Migrated from Stripe to myPOS.
"""

import base64
import logging
import uuid
from urllib.parse import urlparse

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.tenant import SubscriptionPlan, SubscriptionStatus, Tenant
from app.redis_client import redis_client

logger = logging.getLogger("shipflow")

MYPOS_EVENT_TTL = 7 * 24 * 3600
MYPOS_EVENT_KEY_PREFIX = "shipflow:mypos_events:"


def _get_amount(plan: str) -> float:
    """Return myPOS amount for plan (monthly)."""
    if plan == "starter":
        return settings.mypos_amount_starter_monthly or 0.0
    if plan == "professional":
        return settings.mypos_amount_professional_monthly or 0.0
    return 0.0


def _validate_redirect_url(url: str, param_name: str) -> None:
    """Validate redirect URL is from allowed origins. Raises ValueError if not."""
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"{param_name} must use http or https")
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in settings.cors_origins:
            raise ValueError(
                f"{param_name} must be from an allowed origin: {settings.cors_origins}"
            )
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid {param_name}: {e}") from e


def _sign_mypos_request(params: dict, private_key_pem: str) -> str:
    """Sign myPOS request: concat values in params order (excl Signature), base64, RSA-SHA256, base64.

    myPOS verifies using the order parameters appear in the POST body. We must sign with the same
    order we send in the form. See: https://developers.mypos.com/apis/checkout-api/checkout-getting-started/authentication
    """
    keys_in_order = [k for k in params.keys() if k != "Signature"]
    values = [str(params[k]) for k in keys_in_order]
    concat = "-".join(values)
    encoded = base64.b64encode(concat.encode()).decode()
    key = serialization.load_pem_private_key(
        private_key_pem.encode(), password=None, backend=default_backend()
    )
    sig = key.sign(encoded.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


def verify_mypos_notify(data: dict, public_cert_pem: str) -> bool:
    """Verify myPOS notify signature using their public certificate."""
    signature_b64 = data.get("Signature", "")
    if not signature_b64 or not public_cert_pem:
        return False
    sorted_keys = sorted(k for k in data.keys() if k != "Signature")
    values = [str(data[k]) for k in sorted_keys]
    concat = "-".join(values)
    encoded = base64.b64encode(concat.encode()).decode()
    cert = serialization.load_pem_x509_certificate(
        public_cert_pem.encode(), backend=default_backend()
    )
    pub_key = cert.public_key()
    try:
        sig_bytes = base64.b64decode(signature_b64)
        pub_key.verify(sig_bytes, encoded.encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


async def create_checkout_session(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    plan: str,
    success_url: str,
    cancel_url: str,
    customer_email: str | None = None,
) -> dict:
    """Create myPOS checkout params for IPCPurchase redirect flow.

    Returns dict with 'url' and 'form_data' for frontend to POST to myPOS.
    """
    _validate_redirect_url(success_url, "success_url")
    _validate_redirect_url(cancel_url, "cancel_url")

    if not settings.mypos_private_key or not settings.mypos_sid:
        raise ValueError("myPOS is not configured (MYPOS_PRIVATE_KEY or MYPOS_SID missing)")

    amount = _get_amount(plan)
    if amount <= 0:
        raise ValueError(f"Invalid plan or amount not configured: {plan}")

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise ValueError("Tenant not found")

    notify_url = f"{settings.api_public_base_url.rstrip('/')}/api/v1/billing/webhooks/mypos"
    if not settings.api_public_base_url or not notify_url.startswith("https://"):
        raise ValueError(
            "API_PUBLIC_BASE_URL must be set to a public HTTPS URL for myPOS notify callbacks. "
            "For local testing: run 'ngrok http 8000' and set API_PUBLIC_BASE_URL=https://YOUR-ID.ngrok-free.app"
        )

    order_id = f"{tenant_id}-{plan}-{uuid.uuid4().hex[:12]}"

    plan_label = "Starter" if plan == "starter" else "Professional"
    cart_items = 1
    article_1 = f"Portnomic {plan_label} — Monthly"
    quantity_1 = 1
    price_1 = amount
    amount_1 = amount
    currency = settings.mypos_currency

    params: dict[str, str | int | float] = {
        "IPCmethod": "IPCPurchase",
        "IPCVersion": "1.4",
        "IPCLanguage": "EN",
        "SID": settings.mypos_sid,
        "WalletNumber": settings.mypos_wallet_number,
        "KeyIndex": str(settings.mypos_key_index),
        "Amount": f"{amount:.2f}",
        "Currency": currency,
        "OrderID": order_id,
        "URL_OK": success_url,
        "URL_Cancel": cancel_url,
        "URL_Notify": notify_url,
        "CardTokenRequest": "0",
        "PaymentParametersRequired": "2",
        "PaymentMethod": "1",
        "CustomerEmail": customer_email or f"tenant-{tenant_id}@portnomic.ai",
        "Note": f"Portnomic {plan_label} subscription",
        "CartItems": cart_items,
        "Article_1": article_1,
        "Quantity_1": quantity_1,
        "Price_1": f"{price_1:.2f}",
        "Amount_1": f"{amount_1:.2f}",
        "Currency_1": currency,
    }

    signature = _sign_mypos_request(params, settings.mypos_private_key)
    params["Signature"] = signature

    form_data = {k: str(v) for k, v in params.items()}
    return {"url": settings.mypos_base_url.rstrip("/"), "form_data": form_data}


async def create_portal_session(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    return_url: str,
) -> dict:
    """myPOS has no Customer Portal. Return 501-style response handled by router."""
    raise ValueError(
        "Subscription management is not available with myPOS. Contact support for plan changes or cancellations."
    )


async def is_event_processed(order_id: str) -> bool:
    """Check if myPOS notify was already processed (idempotency)."""
    key = f"{MYPOS_EVENT_KEY_PREFIX}{order_id}"
    return await redis_client.exists(key) > 0


async def mark_event_processed(order_id: str) -> None:
    """Mark myPOS notify as processed."""
    key = f"{MYPOS_EVENT_KEY_PREFIX}{order_id}"
    await redis_client.set(key, "1", ex=MYPOS_EVENT_TTL)


def _parse_order_id_for_tenant(order_id: str) -> uuid.UUID | None:
    """Extract tenant_id from OrderID format: {tenant_id}-{plan}-{suffix}."""
    parts = order_id.split("-")
    if len(parts) >= 1:
        try:
            return uuid.UUID(parts[0])
        except ValueError:
            pass
    return None


def _parse_order_id_for_plan(order_id: str) -> str:
    """Extract plan from OrderID format: {tenant_id}-{plan}-{suffix}."""
    parts = order_id.split("-")
    if len(parts) >= 2 and parts[1] in ("starter", "professional"):
        return parts[1]
    return SubscriptionPlan.STARTER.value


async def process_mypos_notify(db: AsyncSession, data: dict) -> None:
    """Handle IPCPurchaseNotify — update tenant plan and status on successful payment."""
    order_id = data.get("OrderID")
    if not order_id:
        logger.warning("myPOS notify missing OrderID")
        return

    tenant_id = _parse_order_id_for_tenant(order_id)
    if not tenant_id:
        logger.warning("myPOS notify could not parse tenant_id from OrderID: %s", order_id)
        return

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        logger.warning("myPOS notify tenant not found: %s", tenant_id)
        return

    plan = _parse_order_id_for_plan(order_id)
    tenant.mypos_order_id = order_id
    tenant.plan = plan
    tenant.subscription_status = SubscriptionStatus.ACTIVE.value
    await db.flush()
    logger.info("myPOS payment success: tenant=%s plan=%s order_id=%s", tenant_id, plan, order_id)


async def get_billing_status(db: AsyncSession, tenant_id: uuid.UUID) -> dict:
    """Get billing status for tenant: plan, subscription_status, usage, limits."""
    from app.config import PLAN_LIMITS
    from app.services.limits import (
        check_ai_parse_limit,
        check_da_limit,
        check_user_limit,
        check_vessel_limit,
    )

    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {
            "plan": "starter",
            "subscription_status": "trial",
            "usage": {"users": 0, "vessels": 0, "das_this_month": 0, "ai_parses_this_month": 0},
            "limits": PLAN_LIMITS.get("starter", {}),
        }

    plan = tenant.plan or "starter"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])

    user_result = await check_user_limit(db, tenant_id)
    vessel_result = await check_vessel_limit(db, tenant_id)
    da_result = await check_da_limit(db, tenant_id)
    ai_result = await check_ai_parse_limit(db, tenant_id)

    return {
        "plan": plan,
        "subscription_status": tenant.subscription_status or "trial",
        "usage": {
            "users": user_result.current,
            "vessels": vessel_result.current,
            "das_this_month": da_result.current,
            "ai_parses_this_month": ai_result.current,
        },
        "limits": {
            "users": limits.get("users"),
            "vessels": limits.get("vessels"),
            "das_per_month": limits.get("das_per_month"),
            "ai_parses_per_month": limits.get("ai_parses_per_month"),
        },
    }
