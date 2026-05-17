"""Integration tests for rate limits, request size, and refresh reuse."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.helpers import cleanup_org_user

pytestmark = pytest.mark.integration


def test_oversized_request_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", "1024")
    from app.core.config import reset_settings_cache

    reset_settings_cache()
    from app.main import create_application

    oversized_client = TestClient(create_application())
    try:
        body = b'{"email":"a@b.com","password":"' + b"x" * 2000 + b'"}'
        r = oversized_client.post(
            "/api/v1/auth/login",
            headers={"Content-Type": "application/json"},
            content=body,
        )
        assert r.status_code == 413, r.text
    finally:
        reset_settings_cache()


def test_refresh_token_reuse_revokes_sessions(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:12]
    email = f"reuse-{suffix}@example.com"
    password = "reusepass1A"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Reuse Org {suffix}",
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code == 200, reg.text
    body = reg.json()
    old_refresh = body["tokens"]["refresh_token"]
    org_id = body["organization"]["id"]
    user_id = body["user"]["id"]

    try:
        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert rotated.status_code == 200, rotated.text
        new_refresh = rotated.json()["tokens"]["refresh_token"]
        assert new_refresh != old_refresh

        reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert reuse.status_code == 401, reuse.text

        new_still_works = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
        assert new_still_works.status_code == 401, new_still_works.text
    finally:
        cleanup_org_user(org_id, user_id)


def test_security_headers_on_api_response(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
