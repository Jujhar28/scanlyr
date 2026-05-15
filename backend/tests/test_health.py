"""Liveness and readiness HTTP endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_health_liveness_root(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_v1_public(client: TestClient) -> None:
    """``GET /api/v1/health`` is declared public (no bearer)."""
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"


def test_health_v1_head_public(client: TestClient) -> None:
    """``HEAD`` is treated like ``GET`` for public ``/api/v1`` routes."""
    r = client.head("/api/v1/health")
    assert r.status_code == 200


@pytest.mark.integration
def test_ready_returns_structured_checks(client: TestClient) -> None:
    """``GET /ready`` probes database, migrations, storage (no auth)."""
    r = client.get("/ready")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert data["status"] in ("ready", "degraded", "not_ready")
    assert "critical_ok" in data
    assert isinstance(data["critical_ok"], bool)
    assert "checks" in data
    for key in ("database", "migrations", "report_storage", "security"):
        assert key in data["checks"]
        chk = data["checks"][key]
        assert chk["status"] in ("pass", "fail", "warn", "skipped", "unknown")
        assert "message" in chk
