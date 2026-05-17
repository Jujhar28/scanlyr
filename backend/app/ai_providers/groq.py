from __future__ import annotations

import logging
from typing import Any

import httpx

from app.ai_providers.base import AIProvider
from app.ai_providers.errors import AIProviderConfigError, AIProviderResponseError
from app.ai_providers.prompts import (
    CYBERSECURITY_SYSTEM_INSTRUCTION,
    HYBRID_REVERIFY_SYSTEM_INSTRUCTION,
    cybersecurity_analysis_prompt,
    hybrid_reverify_prompt,
)
from app.ai_providers.validation import (
    parse_and_validate_analysis_json,
    parse_and_validate_hybrid_reverify_json,
)
from app.ai_providers.retry import execute_with_retries
from app.ai_providers.schemas import HybridReverifyResult, TextAnalysisResult
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Fast Groq models for low-latency classification (override with GROQ_MODEL).
DEFAULT_GROQ_FAST_MODEL = "llama-3.1-8b-instant"


class GroqProvider(AIProvider):
    """
    Groq OpenAI-compatible ``/chat/completions`` adapter.

    Optimized for quick cybersecurity classification via a small fast model.

    Configure via environment:
    - ``GROQ_API_KEY`` (required)
    - ``GROQ_MODEL`` (optional, default ``llama-3.1-8b-instant``)
    """

    provider_id = "groq"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        settings: Settings | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self._api_key = (api_key if api_key is not None else cfg.groq_api_key) or ""
        self._model = model or cfg.groq_model or DEFAULT_GROQ_FAST_MODEL
        self._base_url = (base_url or cfg.groq_api_base_url).rstrip("/")
        self._timeout = timeout_seconds if timeout_seconds is not None else cfg.groq_timeout_seconds
        self._max_retries = max_retries if max_retries is not None else cfg.groq_max_retries
        self._retry_backoff = (
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else cfg.groq_retry_backoff_seconds
        )
        self._client = client

    def analyze_text(self, input_text: str) -> TextAnalysisResult:
        if not self._api_key.strip():
            raise AIProviderConfigError(
                "GROQ_API_KEY is not configured. "
                "Create a key at https://console.groq.com/keys and set GROQ_API_KEY in backend/.env",
            )
        if not input_text.strip():
            raise AIProviderResponseError("input_text must not be empty.")

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = _build_request_body(self._model, input_text)

        def _post() -> httpx.Response:
            if self._client is not None:
                response = self._client.post(url, headers=headers, json=body, timeout=self._timeout)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            return response

        try:
            response = execute_with_retries(
                _post,
                max_attempts=self._max_retries,
                initial_backoff_seconds=self._retry_backoff,
                provider_label="Groq API",
            )
        except AIProviderResponseError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Groq provider failure")
            raise AIProviderResponseError(f"Groq analysis failed: {exc}") from exc

        logger.debug("Groq classification complete model=%s", self._model)
        return parse_and_validate_analysis_json(_extract_groq_content(response.json()))

    def analyze_hybrid_reverify(
        self,
        input_text: str,
        findings: list[dict[str, object]],
    ) -> HybridReverifyResult:
        if not self._api_key.strip():
            raise AIProviderConfigError("GROQ_API_KEY is not configured.")
        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": HYBRID_REVERIFY_SYSTEM_INSTRUCTION},
                {"role": "user", "content": hybrid_reverify_prompt(input_text, findings)},
            ],
        }

        def _post() -> httpx.Response:
            if self._client is not None:
                response = self._client.post(url, headers=headers, json=body, timeout=self._timeout)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            return response

        try:
            response = execute_with_retries(
                _post,
                max_attempts=self._max_retries,
                initial_backoff_seconds=self._retry_backoff,
                provider_label="Groq API",
            )
        except AIProviderResponseError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Groq provider failure")
            raise AIProviderResponseError(f"Groq hybrid re-verify failed: {exc}") from exc

        return parse_and_validate_hybrid_reverify_json(_extract_groq_content(response.json()))


def _build_request_body(model: str, input_text: str) -> dict[str, Any]:
    return {
        "model": model,
        "temperature": 0.1,
        "max_tokens": 512,
        "top_p": 0.9,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": CYBERSECURITY_SYSTEM_INSTRUCTION},
            {"role": "user", "content": cybersecurity_analysis_prompt(input_text)},
        ],
    }


def _extract_groq_content(payload: Any) -> str:
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderResponseError("Unexpected Groq response shape.") from exc
