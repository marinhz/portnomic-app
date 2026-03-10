import uuid
from datetime import datetime, timedelta, timezone

import pyotp
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.role import Role
from app.models.user import User
from app.redis_client import redis_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _get_fernet() -> Fernet:
    return Fernet(settings.mfa_encryption_key.encode())


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user is None:
        pwd_context.hash("dummy")
        return None
    if not pwd_context.verify(password, user.password_hash):
        return None
    return user


def create_access_token(user: User, role: Role) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role_id": str(role.id),
        "permissions": role.permissions or [],
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user: User, jti: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "type": "refresh",
        "jti": jti or str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_refresh_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            return {}
        return payload
    except JWTError:
        return {}


REFRESH_TOKEN_USED_PREFIX = "shipflow:refresh_used:"


async def is_refresh_token_reused(jti: str) -> bool:
    """Check if this refresh token was already used (token reuse = possible theft)."""
    key = f"{REFRESH_TOKEN_USED_PREFIX}{jti}"
    return await redis_client.exists(key) > 0


async def mark_refresh_token_used(jti: str) -> None:
    """Mark refresh token as used. TTL matches token expiry."""
    key = f"{REFRESH_TOKEN_USED_PREFIX}{jti}"
    ttl = settings.jwt_refresh_expiry_minutes * 60  # seconds
    await redis_client.set(key, "1", ex=ttl)


def create_mfa_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "type": "mfa",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_mfa_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "mfa":
            return {}
        return payload
    except JWTError:
        return {}


def encrypt_mfa_secret(secret: str) -> str:
    return _get_fernet().encrypt(secret.encode()).decode()


def decrypt_mfa_secret(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


async def verify_totp(user: User, code: str, db: AsyncSession) -> bool:
    if not user.mfa_secret:
        return False
    plain_secret = decrypt_mfa_secret(user.mfa_secret)
    totp = pyotp.TOTP(plain_secret)
    return totp.verify(code, valid_window=1)


def setup_mfa(user: User) -> tuple[str, str]:
    """Generate a new TOTP secret and provisioning URI.

    Returns (encrypted_secret, provisioning_uri).
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="Portnomic")
    encrypted = encrypt_mfa_secret(secret)
    return encrypted, uri


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_policy(password: str) -> str | None:
    """Returns error message if password fails policy, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters"
    return None
