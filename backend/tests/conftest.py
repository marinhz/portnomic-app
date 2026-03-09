"""Pytest configuration and fixtures for Portnomic backend tests."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure platform admin is set for tests that need it
os.environ.setdefault("PLATFORM_ADMIN_EMAILS", "admin@portnomic.ai")


@pytest.fixture
def anyio_backend():
    return "asyncio"
