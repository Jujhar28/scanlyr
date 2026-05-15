"""Scan session lifecycle via the synthetic detection pipeline."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.helpers import cleanup_org_user

pytestmark = pytest.mark.integration


def test_scan_session_created_and_linked_to_detection_events(client: TestClient) -> None:
    """Pipeline creates a completed scan session; listing detections shows linked events."""
    suffix = uuid.uuid4().hex[:12]
    email = f"scan-sess-{suffix}@example.com"
    password = "scanpass1A"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Scan Session Org {suffix}",
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code == 200, reg.text
    body = reg.json()
    token = body["tokens"]["access_token"]
    org_id = body["organization"]["id"]
    user_id = body["user"]["id"]
    auth = {"Authorization": f"Bearer {token}"}

    try:
        pipe = client.post(
            "/api/v1/detections/pipeline",
            headers=auth,
            json={"mode": "synthetic", "synthetic_event_count": 2},
        )
        assert pipe.status_code == 200, pipe.text
        scan_id = pipe.json()["scan_session_id"]

        lst = client.get("/api/v1/detections", headers=auth, params={"limit": 50})
        assert lst.status_code == 200, lst.text
        items = lst.json()["items"]
        linked = [
            e
            for e in items
            if e.get("scan_session_id") is not None
            and str(e["scan_session_id"]) == str(scan_id)
        ]
        assert len(linked) >= 2
    finally:
        cleanup_org_user(org_id, user_id)
