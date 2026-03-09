import hashlib
import uuid
from datetime import datetime, timezone

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.middleware.metrics import auth_login_attempts_total, auth_login_failures_total
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUser,
    LoginRequest,
    LoginResponse,
    MfaConfirmRequest,
    MfaDisableRequest,
    MfaRequest,
    MfaSetupResponse,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.common import ErrorResponse, SingleResponse
from app.services import audit as audit_svc
from app.services import auth as auth_svc

from app.config import settings as app_settings
from slowapi import Limiter
from slowapi.util import get_remote_address

auth_limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().encode()).hexdigest()[:12]


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
@auth_limiter.limit(f"{app_settings.rate_limit_auth_per_minute}/minute")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    user = await auth_svc.authenticate_user(db, body.email, body.password)
    if user is None:
        auth_login_attempts_total.labels(status="failure", tenant_id="").inc()
        auth_login_failures_total.labels(
            reason="invalid_credentials", tenant_id="", user_email_hash=_email_hash(body.email)
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}},
        )

    if user.mfa_enabled:
        auth_login_attempts_total.labels(
            status="mfa_required", tenant_id=str(user.tenant_id)
        ).inc()
        mfa_token = auth_svc.create_mfa_token(user)
        return LoginResponse(
            access_token="",
            refresh_token="",
            expires_in=0,
            requires_mfa=True,
            mfa_token=mfa_token,
        )

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one()

    access_token = auth_svc.create_access_token(user, role)
    refresh_token = auth_svc.create_refresh_token(user)

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    auth_login_attempts_total.labels(
        status="success", tenant_id=str(user.tenant_id)
    ).inc()

    await audit_svc.log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="login",
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    from app.config import settings

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_expiry_minutes * 60,
    )


@router.post(
    "/mfa",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
@auth_limiter.limit(f"{app_settings.rate_limit_auth_per_minute}/minute")
async def verify_mfa(
    body: MfaRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    payload = auth_svc.verify_mfa_token(body.mfa_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_MFA_TOKEN", "message": "Invalid or expired MFA token"}},
        )

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found or inactive"}},
        )

    is_valid = await auth_svc.verify_totp(user, body.code, db)
    if not is_valid:
        auth_login_failures_total.labels(
            reason="invalid_mfa", tenant_id=str(user.tenant_id), user_email_hash=_email_hash(user.email)
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_MFA_CODE", "message": "Invalid TOTP code"}},
        )

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one()

    access_token = auth_svc.create_access_token(user, role)
    refresh_token = auth_svc.create_refresh_token(user)

    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    auth_login_attempts_total.labels(
        status="success", tenant_id=str(user.tenant_id)
    ).inc()

    await audit_svc.log_action(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action="mfa_login",
        resource_type="auth",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    from app.config import settings

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_expiry_minutes * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
@auth_limiter.limit(f"{app_settings.rate_limit_auth_per_minute}/minute")
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    payload = auth_svc.verify_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"}},
        )

    jti = payload.get("jti")
    if jti and await auth_svc.is_refresh_token_reused(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "REFRESH_TOKEN_REUSED", "message": "Token reuse detected"}},
        )
    if jti:
        await auth_svc.mark_refresh_token_used(jti)

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found or inactive"}},
        )

    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one()

    access_token = auth_svc.create_access_token(user, role)
    new_refresh_token = auth_svc.create_refresh_token(user)

    from app.config import settings

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_expiry_minutes * 60,
        refresh_token=new_refresh_token,
    )


@router.get(
    "/me",
    response_model=SingleResponse[CurrentUser],
)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
) -> SingleResponse[CurrentUser]:
    return SingleResponse(data=current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(User).where(User.id == current_user.id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    if not auth_svc.pwd_context.verify(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_PASSWORD",
                    "message": "Current password is incorrect",
                }
            },
        )
    policy_error = auth_svc.validate_password_policy(body.new_password)
    if policy_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "PASSWORD_POLICY", "message": policy_error}},
        )
    user.password_hash = auth_svc.hash_password(body.new_password)


@router.get(
    "/mfa/setup",
    response_model=SingleResponse[MfaSetupResponse],
)
async def mfa_setup(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SingleResponse[MfaSetupResponse]:
    result = await db.execute(
        select(User).where(User.id == current_user.id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "MFA_ALREADY_ENABLED", "message": "MFA is already enabled"},
            },
        )
    encrypted_secret, provisioning_uri = auth_svc.setup_mfa(user)
    user.mfa_secret = encrypted_secret
    await db.flush()
    totp = pyotp.TOTP(auth_svc.decrypt_mfa_secret(encrypted_secret))
    return SingleResponse(
        data=MfaSetupResponse(secret=totp.secret, provisioning_uri=provisioning_uri)
    )


@router.post("/mfa/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_confirm(
    body: MfaConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(User).where(User.id == current_user.id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "MFA_ALREADY_ENABLED", "message": "MFA is already enabled"},
            },
        )
    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MFA_SETUP_REQUIRED",
                    "message": "Call GET /auth/mfa/setup first to start MFA setup",
                }
            },
        )
    is_valid = await auth_svc.verify_totp(user, body.code, db)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_MFA_CODE", "message": "Invalid TOTP code"}},
        )
    user.mfa_enabled = True


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def mfa_disable(
    body: MfaDisableRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    if not body.password and not body.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "AUTH_REQUIRED",
                    "message": "Password or TOTP code required to disable MFA",
                }
            },
        )
    result = await db.execute(
        select(User).where(User.id == current_user.id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User not found"}},
        )
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"code": "MFA_NOT_ENABLED", "message": "MFA is not enabled"},
            },
        )
    verified = False
    if body.password:
        verified = auth_svc.pwd_context.verify(body.password, user.password_hash)
    elif body.code:
        verified = await auth_svc.verify_totp(user, body.code, db)
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Password or TOTP code is incorrect",
                }
            },
        )
    user.mfa_secret = None
    user.mfa_enabled = False
