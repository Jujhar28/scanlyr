"""Shared pytest fixtures for the backend test suite."""
from __future__ import annotations

import os
import uuid
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Set required environment variables BEFORE any app module is imported.
# config.py has a module-level `settings = get_settings()` that fires at
# collection time, so we need these in os.environ before that happens.
# ---------------------------------------------------------------------------

_REQUIRED_TEST_ENV = {
    "SECRET_KEY": "test-secret-key-that-is-long-enough-for-tests",
    "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/testdb",
}
for _k, _v in _REQUIRED_TEST_ENV.items():
    os.environ.setdefault(_k, _v)

MINIMAL_ENV = _REQUIRED_TEST_ENV


@pytest.fixture(autouse=False)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove any env vars that might bleed in from a real .env during tests."""
    for key in list(os.environ):
        if key.upper() in {
            "SECRET_KEY",
            "DATABASE_URL",
            "APP_ENV",
            "DEBUG",
            "ENABLE_OPENAPI_DOCS",
            "CORS_ORIGINS",
            "BCRYPT_ROUNDS",
        }:
            monkeypatch.delenv(key, raising=False)


@pytest.fixture()
def minimal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the bare minimum env vars for a valid Settings instance."""
    for k, v in MINIMAL_ENV.items():
        monkeypatch.setenv(k, v)


@pytest.fixture()
def mock_db_session() -> MagicMock:
    """A mock SQLAlchemy Session."""
    session = MagicMock()
    return session


@pytest.fixture()
def sample_user_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture()
def sample_org_id() -> uuid.UUID:
    return uuid.UUID("87654321-4321-8765-4321-876543218765")