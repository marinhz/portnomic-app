"""Tests for encryption service (tenant API key encryption)."""

import pytest
from cryptography.fernet import Fernet

from app.services.encryption import (
    decrypt_api_key,
    encrypt_api_key,
    mask_api_key_for_log,
)


def test_encrypt_decrypt_roundtrip(monkeypatch):
    """encrypt_api_key and decrypt_api_key work correctly."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", key)

    plain = "sk-proj-abc123secret"
    encrypted = encrypt_api_key(plain)
    assert encrypted != plain
    assert "sk-" not in encrypted

    decrypted = decrypt_api_key(encrypted)
    assert decrypted == plain


def test_encrypt_empty_returns_empty(monkeypatch):
    """Empty or whitespace input returns empty string."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", key)

    assert encrypt_api_key("") == ""
    assert encrypt_api_key("   ") == ""


def test_decrypt_empty_returns_empty(monkeypatch):
    """Empty encrypted input returns empty string."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", key)

    assert decrypt_api_key("") == ""
    assert decrypt_api_key("   ") == ""


def test_decrypt_wrong_key_raises(monkeypatch):
    """Decryption with wrong key raises ValueError, no key material in message."""
    key1 = Fernet.generate_key().decode()
    key2 = Fernet.generate_key().decode()
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", key1)

    encrypted = encrypt_api_key("sk-secret")
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", key2)

    with pytest.raises(ValueError) as exc_info:
        decrypt_api_key(encrypted)
    assert "sk-" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)


def test_decrypt_invalid_token_raises(monkeypatch):
    """Invalid token raises ValueError."""
    key = Fernet.generate_key().decode()
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", key)

    with pytest.raises(ValueError):
        decrypt_api_key("not-valid-fernet-token")


def test_encrypt_missing_key_raises(monkeypatch):
    """Encrypt without key raises ValueError."""
    monkeypatch.setattr("app.services.encryption.settings.llm_key_encryption_key", "")

    with pytest.raises(ValueError) as exc_info:
        encrypt_api_key("sk-secret")
    assert "LLM_KEY_ENCRYPTION_KEY" in str(exc_info.value)


def test_mask_api_key_for_log():
    """mask_api_key_for_log never exposes full key."""
    assert mask_api_key_for_log("sk-proj-abc123") == "sk-p...xxxx"
    assert mask_api_key_for_log("sk-abc") == "sk-a...xxxx"
    assert mask_api_key_for_log(None) == "...xxxx"
    assert mask_api_key_for_log("") == "...xxxx"
    assert mask_api_key_for_log("abc") == "...xxxx"  # short keys get full mask
