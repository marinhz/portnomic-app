"""
Integration test: Tenant isolation.

Verifies that Tenant A cannot access Tenant B's data via API.
Requires: database with seed data, PLATFORM_ADMIN_EMAILS=admin@portnomic.ai
Run: pytest tests/test_tenant_isolation.py -v
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_tenant_a_cannot_access_tenant_b_vessels():
    """Tenant A user cannot list or access Tenant B's vessels."""
    slug = f"tenant-b-{uuid.uuid4().hex[:8]}"
    with TestClient(app) as client:
        # 1. Login as platform admin (tenant A - from seed)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@portnomic.ai", "password": "admin123"},
        )
        assert login_resp.status_code == 200
        token_a = login_resp.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. Create tenant B with initial admin
        create_resp = client.post(
            "/api/v1/platform/tenants",
            headers=headers_a,
            json={
                "name": "Tenant B Corp",
                "slug": slug,
                "initial_admin_email": "admin_b@test.isolation",
                "initial_admin_password": "testpass123",
            },
        )
        assert create_resp.status_code == 201
        create_resp.json()["data"]["id"]

        # 3. Login as tenant B admin
        login_b_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin_b@test.isolation",
                "password": "testpass123",
            },
        )
        assert login_b_resp.status_code == 200
        token_b = login_b_resp.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 4. Create a vessel in tenant B
        vessel_resp = client.post(
            "/api/v1/vessels",
            headers=headers_b,
            json={"name": "Vessel B1", "imo": "9999999"},
        )
        assert vessel_resp.status_code == 201
        vessel_b_id = vessel_resp.json()["data"]["id"]

        # 5. Tenant A tries to access Tenant B's vessel - should get 404
        get_resp = client.get(
            f"/api/v1/vessels/{vessel_b_id}",
            headers=headers_a,
        )
        assert get_resp.status_code == 404

        # 6. Tenant A's vessel list should not include Tenant B's vessel
        list_resp = client.get(
            "/api/v1/vessels",
            headers=headers_a,
        )
        assert list_resp.status_code == 200
        vessel_ids = [v["id"] for v in list_resp.json()["data"]]
        assert vessel_b_id not in vessel_ids
