"""Pytest fixtures.

Run from ``backend`` so ``.env`` loads and ``alembic`` finds ``alembic.ini``::

    cd backend
    .\\.venv\\Scripts\\activate
    pytest tests -q

Optional **dedicated test DB** (recommended): set ``TEST_DATABASE_URL`` *before*
starting pytest so it replaces ``DATABASE_URL`` before the app module builds the
SQLAlchemy engine::

    set TEST_DATABASE_URL=postgresql://user:pass@127.0.0.1:5432/shadowtest
    pytest tests -q

Then run ``alembic upgrade head`` against that database once (or in CI before tests).
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Apply test DB URL before importing the app (engine + Settings are created on import).
if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def database_url() -> str:
    """Effective database URL (from Settings — includes ``.env`` loaded at app import)."""
    from app.core.config import settings

    url = settings.database_url.strip()
    if not url:
        pytest.skip("database_url is empty; configure DATABASE_URL or TEST_DATABASE_URL.")
    return url


@pytest.fixture(autouse=True)
def scan_integration_rules_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep POST /scan integration tests deterministic (no live Gemini/Groq calls)."""
    monkeypatch.setattr(
        "app.services.scan_text_service.try_ai_scan_analysis",
        lambda *_args, **_kwargs: None,
    )


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
