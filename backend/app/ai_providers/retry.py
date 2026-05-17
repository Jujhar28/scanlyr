"""HTTP retry helpers for AI provider adapters."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import httpx

from app.ai_providers.errors import AIProviderResponseError, AIProviderTimeoutError

T = TypeVar("T")

DEFAULT_RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})


def execute_with_retries(
    operation: Callable[[], T],
    *,
    max_attempts: int = 3,
    initial_backoff_seconds: float = 1.0,
    max_backoff_seconds: float = 8.0,
    retryable_statuses: frozenset[int] = DEFAULT_RETRYABLE_STATUS,
    provider_label: str = "API",
) -> T:
    """
    Run ``operation`` with exponential backoff on transient HTTP/network failures.

    Non-retryable HTTP errors and the last failed attempt are raised as
    :class:`AIProviderResponseError`.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except httpx.HTTPStatusError as exc:
            last_error = exc
            status = exc.response.status_code
            if status not in retryable_statuses or attempt >= max_attempts:
                raise AIProviderResponseError(
                    _format_http_error(provider_label, exc),
                ) from exc
        except httpx.TimeoutException as exc:
            last_error = exc
            if attempt >= max_attempts:
                raise AIProviderTimeoutError(
                    f"{provider_label} timed out after {max_attempts} attempt(s): {exc}",
                ) from exc
        except (httpx.NetworkError, httpx.ConnectError) as exc:
            last_error = exc
            if attempt >= max_attempts:
                raise AIProviderResponseError(
                    f"{provider_label} request failed after {max_attempts} attempts: {exc}",
                ) from exc

        delay = min(initial_backoff_seconds * (2 ** (attempt - 1)), max_backoff_seconds)
        time.sleep(delay)

    raise AIProviderResponseError(
        f"{provider_label} request failed after {max_attempts} attempts: {last_error}",
    )


def _format_http_error(provider_label: str, exc: httpx.HTTPStatusError) -> str:
    body = exc.response.text[:500].strip()
    detail = f" — {body}" if body else ""
    return f"{provider_label} error {exc.response.status_code}{detail}"
