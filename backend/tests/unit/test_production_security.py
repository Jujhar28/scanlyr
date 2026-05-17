"""Unit tests for production security middleware and helpers."""

from __future__ import annotations

import pytest
from starlette.requests import Request

from app.core.config import Settings, reset_settings_cache
from app.middleware.rate_limit import _RateLimitStore
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.services.request_context import client_ip_from_request


def test_client_ip_trusts_forwarded_for(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    reset_settings_cache()
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"x-forwarded-for", b"203.0.113.10, 10.0.0.1")],
        "client": ("127.0.0.1", 12345),
    }
    request = Request(scope)
    assert client_ip_from_request(request) == "203.0.113.10"
    reset_settings_cache()


def test_rate_limit_store_blocks_over_limit() -> None:
    store = _RateLimitStore()
    key = "test-ip"
    for _ in range(3):
        allowed, _ = store.allow(key, limit=3)
        assert allowed
    allowed, retry = store.allow(key, limit=3)
    assert not allowed
    assert retry >= 1


def test_production_settings_reject_weak_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "change-me-in-production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost/db")
    reset_settings_cache()
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings()
    reset_settings_cache()


def test_security_headers_include_csp_for_api() -> None:
    import asyncio

    from starlette.responses import Response

    async def call_next(_request: Request) -> Response:
        return Response(status_code=200)

    scope = {"type": "http", "method": "GET", "path": "/api/v1/health", "headers": [], "client": ("127.0.0.1", 1)}
    request = Request(scope)
    middleware = SecurityHeadersMiddleware(app=object())  # type: ignore[arg-type]
    response = asyncio.run(middleware.dispatch(request, call_next))
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "default-src" in (response.headers.get("Content-Security-Policy") or "")
