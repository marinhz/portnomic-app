"""Tests for tenant LLM config service (encryption integration)."""

import uuid

from cryptography.fernet import Fernet

from app.models.tenant_llm_config import TenantLlmConfig
from app.services.encryption import encrypt_api_key
from app.services.tenant_llm_config_svc import get_decrypted_llm_credentials


def test_get_decrypted_llm_credentials_none_config():
    """Returns None when config is None."""
    assert get_decrypted_llm_credentials(None) is None


def test_get_decrypted_llm_credentials_disabled():
    """Returns None when config is disabled (no decryption needed)."""
    config = TenantLlmConfig(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        api_key_encrypted="some-encrypted-value",
        base_url="https://api.example.com",
        model="gpt-4",
        enabled=False,
    )
    assert get_decrypted_llm_credentials(config) is None


def test_get_decrypted_llm_credentials_no_key():
    """Returns None when no api_key_encrypted."""
    config = TenantLlmConfig(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        api_key_encrypted=None,
        base_url="https://api.example.com",
        model="gpt-4",
        enabled=True,
    )
    assert get_decrypted_llm_credentials(config) is None


def test_get_decrypted_llm_credentials_success(monkeypatch):
    """Returns (api_key, base_url, model) when config valid."""
    from app.config import settings

    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "llm_key_encryption_key", key)

    encrypted = encrypt_api_key("sk-my-secret-key")

    config = TenantLlmConfig(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        api_key_encrypted=encrypted,
        base_url="https://custom.api.com",
        model="gpt-4o",
        enabled=True,
    )

    creds = get_decrypted_llm_credentials(config)
    assert creds is not None
    api_key, base_url, model = creds
    assert api_key == "sk-my-secret-key"
    assert base_url == "https://custom.api.com"
    assert model == "gpt-4o"


def test_get_decrypted_llm_credentials_uses_platform_defaults(monkeypatch):
    """Uses platform base_url and model when config has None."""
    from app.config import settings

    key = Fernet.generate_key().decode()
    monkeypatch.setattr(settings, "llm_key_encryption_key", key)

    encrypted = encrypt_api_key("sk-secret")

    config = TenantLlmConfig(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        api_key_encrypted=encrypted,
        base_url=None,
        model=None,
        enabled=True,
    )

    creds = get_decrypted_llm_credentials(config)
    assert creds is not None
    _, base_url, model = creds
    assert base_url == settings.llm_api_url
    assert model == settings.llm_model
