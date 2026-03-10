"""Encryption service for sensitive data at rest (e.g. tenant API keys).

Key rotation: To rotate ENCRYPTION_KEY / LLM_KEY_ENCRYPTION_KEY:
1. Generate new key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
2. For each tenant_llm_config with api_key_encrypted: decrypt with old key, re-encrypt with new key
3. Update env with new key; restart services
4. Defer full automation if time-boxed; manual migration script is acceptable.
"""

import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger("shipflow.encryption")

# Mask for safe log output (e.g. "sk-...xxxx")
MASK_SUFFIX = "...xxxx"


def _get_fernet() -> Fernet:
    """Build Fernet instance from config key. Raises if key invalid."""
    raw = settings.llm_key_encryption_key
    if not raw or not raw.strip():
        raise ValueError(
            "LLM_KEY_ENCRYPTION_KEY is required for tenant API key encryption; "
            'generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    raw = raw.strip()
    try:
        key = raw.encode() if isinstance(raw, str) else raw
        return Fernet(key)
    except Exception as e:
        raise ValueError(
            f"Invalid LLM_KEY_ENCRYPTION_KEY: {type(e).__name__}. "
            "Use Fernet.generate_key().decode() for a valid key."
        ) from e


def encrypt_api_key(plain: str) -> str:
    """Encrypt a plain API key for storage. Never log the plain value."""
    if not plain or not plain.strip():
        return ""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain.strip().encode("utf-8"))
    return encrypted.decode("ascii")


def decrypt_api_key(encrypted: str) -> str:
    """Decrypt an API key. On failure, log generic error and raise ValueError.

    Never log key material. Caller should treat as 'key invalid'.
    """
    if not encrypted or not encrypted.strip():
        return ""
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted.strip().encode("ascii"))
        return decrypted.decode("utf-8")
    except InvalidToken:
        logger.warning("API key decryption failed (invalid token or wrong key)")
        raise ValueError("API key decryption failed; key may be invalid or rotated") from None
    except Exception as exc:
        logger.warning("API key decryption failed: %s", type(exc).__name__)
        raise ValueError("API key decryption failed; key may be invalid or rotated") from exc


def mask_api_key_for_log(api_key: str | None) -> str:
    """Return a safe mask for logging, e.g. 'sk-...xxxx'. Never log full key."""
    if not api_key or len(api_key) < 4:
        return MASK_SUFFIX
    prefix = api_key[:4] if api_key.startswith("sk-") else api_key[:3]
    return f"{prefix}{MASK_SUFFIX}"
