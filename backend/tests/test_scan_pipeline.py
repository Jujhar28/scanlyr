"""Full synthetic pipeline: session → events → scores → report."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.helpers import cleanup_org_user

pytestmark = pytest.mark.integration


def test_synthetic_scan_pipeline_creates_session_events_scores_report(client: TestClient) -> None:
    suffix = uuid.uuid4().hex[:12]
    email = f"pipeline-{suffix}@example.com"
    password = "pipeline1A"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Pipeline Org {suffix}",
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code == 200, reg.text
    body = reg.json()
    token = body["tokens"]["access_token"]
    org_id = body["organization"]["id"]
    user_id = body["user"]["id"]

    try:
        pipe = client.post(
            "/api/v1/detections/pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json={"mode": "synthetic", "synthetic_event_count": 2},
        )
        assert pipe.status_code == 200, pipe.text
        data = pipe.json()
        assert data["mode"] == "synthetic"
        assert data["detection_events_inserted"] == 2
        assert data["risk_scores_created"] == 4
        assert data["report"]["id"]
        assert data["report"]["status"] == "ready"
        assert data["report"]["downloadable"] is True
    finally:
        cleanup_org_user(org_id, user_id)
