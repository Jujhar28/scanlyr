"""Shared helpers for integration tests (PostgreSQL)."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.user import User


def cleanup_org_user(org_id: str, user_id: str) -> None:
    """Remove org (cascades tenant data) and user; call after integration tests."""
    oid = UUID(org_id)
    uid = UUID(user_id)
    db = SessionLocal()
    try:
        db.execute(delete(RefreshToken).where(RefreshToken.user_id == uid))
        db.execute(delete(Organization).where(Organization.id == oid))
        db.execute(delete(User).where(User.id == uid))
        db.commit()
    finally:
        db.close()


@contextmanager
def registered_admin_user(
    client: TestClient,
    *,
    suffix: str | None = None,
) -> Generator[dict[str, Any], None, None]:
    """Register a new org+admin user; yield token/org/user/email; cleanup on exit."""
    suf = suffix or uuid.uuid4().hex[:12]
    email = f"pytest-{suf}@example.com"
    password = "pytest1Pass"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": f"Pytest Org {suf}",
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code == 200, reg.text
    body = reg.json()
    ctx = {
        "email": email,
        "password": password,
        "access_token": body["tokens"]["access_token"],
        "organization_id": body["organization"]["id"],
        "user_id": body["user"]["id"],
    }
    try:
        yield ctx
    finally:
        cleanup_org_user(ctx["organization_id"], ctx["user_id"])
