"""Retry helper unit tests."""

from __future__ import annotations

import httpx
import pytest

from app.ai_providers.errors import AIProviderResponseError
from app.ai_providers.retry import execute_with_retries


def test_execute_with_retries_succeeds_after_transient_error() -> None:
    attempts = {"n": 0}

    def operation() -> str:
        attempts["n"] += 1
        if attempts["n"] < 2:
            request = httpx.Request("POST", "https://example.com")
            response = httpx.Response(503, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)
        return "ok"

    assert (
        execute_with_retries(
            operation,
            max_attempts=3,
            initial_backoff_seconds=0.01,
            provider_label="Test",
        )
        == "ok"
    )
    assert attempts["n"] == 2


def test_execute_with_retries_non_retryable_status() -> None:
    def operation() -> None:
        request = httpx.Request("POST", "https://example.com")
        response = httpx.Response(400, request=request)
        raise httpx.HTTPStatusError("bad request", request=request, response=response)

    with pytest.raises(AIProviderResponseError, match="400"):
        execute_with_retries(operation, max_attempts=3, initial_backoff_seconds=0.01)
