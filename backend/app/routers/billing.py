"""Billing router — myPOS Web Checkout, notify webhook.

Task 8.6: Migrated from Stripe to myPOS.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.database import get_db
from app.dependencies.rbac import RequirePermission
from app.dependencies.tenant import get_tenant_id
from app.schemas.auth import CurrentUser
from app.services import billing as billing_svc

logger = logging.getLogger("shipflow")

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


# ── Schemas ────────────────────────────────────────────────────────────────────


class CreateCheckoutSessionRequest(BaseModel):
    plan: str  # "starter" | "professional"
    success_url: str
    cancel_url: str


class CreatePortalSessionRequest(BaseModel):
    return_url: str


# ── Authenticated routes (require billing:manage) ───────────────────────────────


@router.get("/status")
async def get_billing_status(
    current_user: CurrentUser = Depends(
        RequirePermission("billing:manage", allow_platform_admin=True)
    ),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return plan, subscription_status, usage, and limits for tenant."""
    try:
        return await billing_svc.get_billing_status(db=db, tenant_id=tenant_id)
    except Exception as e:
        logger.exception("get_billing_status failed for tenant_id=%s", tenant_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BILLING_STATUS_ERROR",
                    "message": str(e) if settings.environment != "production" else "Failed to load billing status",
                }
            },
        )


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CreateCheckoutSessionRequest,
    current_user: CurrentUser = Depends(
        RequirePermission("billing:manage", allow_platform_admin=True)
    ),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Create myPOS checkout session for plan purchase.

    Returns url and form_data; frontend POSTs form to url to redirect to myPOS.
    """
    if body.plan not in ("starter", "professional"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "INVALID_PLAN", "message": "Plan must be starter or professional"}
            },
        )

    try:
        result = await billing_svc.create_checkout_session(
            db=db,
            tenant_id=tenant_id,
            plan=body.plan,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            customer_email=current_user.email,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "BILLING_ERROR", "message": str(e)}},
        )


@router.post("/portal")
async def create_portal_session(
    body: CreatePortalSessionRequest,
    current_user: CurrentUser = Depends(
        RequirePermission("billing:manage", allow_platform_admin=True)
    ),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """myPOS has no Customer Portal. Returns 501 with contact-support message."""
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": "PORTAL_UNAVAILABLE",
                "message": "Subscription management is not available with myPOS. Contact support for plan changes or cancellations.",
            }
        },
    )


# ── Cancel return (no auth; myPOS POSTs here, we redirect to frontend) ─────────────


@router.post("/cancel-return", response_model=None)
async def billing_cancel_return(request: Request) -> RedirectResponse | PlainTextResponse:
    """Handle myPOS cancel redirect.

    myPOS sends POST with Amount, Currency, OrderID, Signature when user cancels.
    We verify signature (if cert configured), then redirect to frontend billing page.
    """
    if not settings.cors_origins:
        logger.warning("CORS_ORIGINS not configured for cancel redirect")
        return PlainTextResponse(
            content="NOT_CONFIGURED", status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    form = await request.form()
    data = dict(form)

    if settings.mypos_skip_cancel_verify:
        logger.info("myPOS cancel: skipping signature verification (MYPOS_SKIP_CANCEL_VERIFY)")
    elif settings.mypos_public_cert:
        if not billing_svc.verify_mypos_cancel(data, settings.mypos_public_cert):
            logger.warning("myPOS cancel signature verification failed")
            return PlainTextResponse(
                content="INVALID_SIGNATURE", status_code=status.HTTP_400_BAD_REQUEST
            )

    frontend_origin = settings.cors_origins[0].rstrip("/")
    redirect_url = f"{frontend_origin}/settings/billing?canceled=1"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


# ── Webhook (no auth; verify via myPOS RSA signature) ─────────────────────────────


@router.post("/webhooks/mypos")
async def mypos_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    """Handle myPOS IPCPurchaseNotify callback.

    Verifies RSA signature, processes idempotently by OrderID.
    Must return HTTP 200 with body 'OK' or myPOS will reverse the payment.
    """
    if not settings.mypos_public_cert:
        logger.warning("myPOS public cert not configured")
        return PlainTextResponse(
            content="NOT_CONFIGURED", status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    form = await request.form()
    data = dict(form)

    if not billing_svc.verify_mypos_notify(data, settings.mypos_public_cert):
        logger.warning("myPOS notify signature verification failed")
        return PlainTextResponse(
            content="INVALID_SIGNATURE", status_code=status.HTTP_400_BAD_REQUEST
        )

    order_id = data.get("OrderID")
    if not order_id:
        return PlainTextResponse(
            content="MISSING_ORDER_ID", status_code=status.HTTP_400_BAD_REQUEST
        )

    if await billing_svc.is_event_processed(order_id):
        return PlainTextResponse(content="OK")

    try:
        await billing_svc.process_mypos_notify(db, data)
        await billing_svc.mark_event_processed(order_id)
    except Exception:
        logger.exception("Error processing myPOS notify for OrderID %s", order_id)
        return PlainTextResponse(
            content="PROCESSING_ERROR", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return PlainTextResponse(content="OK")
