"""Auth integration: register, login, JWT middleware, protected ``/me``."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.helpers import cleanup_org_user

pytestmark = pytest.mark.integration


def test_register_login_me_and_middleware(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:12]
    email = f"auth-e2e-{suffix}@example.com"
    password = "testpass1A"
    org_name = f"E2E Org {suffix}"

    reg = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": org_name,
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code == 200, reg.text
    body = reg.json()
    assert body["user"]["email"] == email
    assert body["organization"]["name"] == org_name
    assert body["role"] == "admin"
    assert body["tokens"]["token_type"] == "bearer"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]

    access = body["tokens"]["access_token"]
    org_id = body["organization"]["id"]
    user_id = body["user"]["id"]

    try:
        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert me.status_code == 200, me.text
        me_body = me.json()
        assert me_body["user"]["email"] == email
        assert me_body["organization"]["id"] == org_id
        assert me_body["role"] == "admin"

        no_auth = client.get("/api/v1/auth/me")
        assert no_auth.status_code == 401
        err = no_auth.json()
        assert err.get("code") == "authentication_error"
        assert "request_id" in err

        bad = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not-a-real-jwt"},
        )
        assert bad.status_code == 401
        assert bad.json().get("code") == "authentication_error"

        log = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert log.status_code == 200, log.text
        assert log.json()["tokens"]["access_token"]

        wrong_pw = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrongpassword1"},
        )
        assert wrong_pw.status_code == 401

        refr = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": body["tokens"]["refresh_token"]},
        )
        assert refr.status_code == 200, refr.text
        new_access = refr.json()["tokens"]["access_token"]
        assert new_access
        me_after_refresh = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert me_after_refresh.status_code == 200

        dup = client.post(
            "/api/v1/auth/register",
            json={
                "organization_name": "Other",
                "email": email,
                "password": "otherpass1B",
            },
        )
        assert dup.status_code == 409
    finally:
        cleanup_org_user(org_id, user_id)


def test_public_auth_routes_without_bearer(client: TestClient) -> None:
    """Handlers marked ``@public_api_route`` accept no Authorization header (validation still applies)."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "x",
            "email": "not-an-email",
            "password": "short",
        },
    )
    assert r.status_code == 422

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever1"},
    )
    assert login.status_code == 401
