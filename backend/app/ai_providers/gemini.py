from __future__ import annotations

import logging
from typing import Any

import httpx

from app.ai_providers.base import AIProvider
from app.ai_providers.errors import AIProviderConfigError, AIProviderResponseError
from app.ai_providers.prompts import (
    CYBERSECURITY_RESPONSE_SCHEMA,
    CYBERSECURITY_SYSTEM_INSTRUCTION,
    HYBRID_REVERIFY_RESPONSE_SCHEMA,
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

# Default: Gemini 2.0 Flash (Google AI Studio free tier). Override with GEMINI_MODEL.
DEFAULT_GEMINI_FLASH_MODEL = "gemini-2.0-flash"

_BLOCKED_FINISH_REASONS = frozenset(
    {
        "SAFETY",
        "RECITATION",
        "BLOCKLIST",
        "PROHIBITED_CONTENT",
        "SPII",
        "LANGUAGE",
    },
)


class GeminiProvider(AIProvider):
    """
    Google Gemini ``generateContent`` adapter.

    Configure via environment:
    - ``GEMINI_API_KEY`` (required)
    - ``GEMINI_MODEL`` (optional, default ``gemini-2.0-flash``)
  """

    provider_id = "gemini"

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
        self._api_key = (api_key if api_key is not None else cfg.gemini_api_key) or ""
        self._model = model or cfg.gemini_model or DEFAULT_GEMINI_FLASH_MODEL
        self._base_url = (base_url or cfg.gemini_api_base_url).rstrip("/")
        self._timeout = timeout_seconds if timeout_seconds is not None else cfg.ai_provider_timeout_seconds
        self._max_retries = max_retries if max_retries is not None else cfg.gemini_max_retries
        self._retry_backoff = (
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else cfg.gemini_retry_backoff_seconds
        )
        self._client = client

    def analyze_text(self, input_text: str) -> TextAnalysisResult:
        if not self._api_key.strip():
            raise AIProviderConfigError(
                "GEMINI_API_KEY is not configured. "
                "Create a key at https://aistudio.google.com/apikey and set GEMINI_API_KEY in backend/.env",
            )
        if not input_text.strip():
            raise AIProviderResponseError("input_text must not be empty.")

        url = f"{self._base_url}/v1beta/models/{self._model}:generateContent"
        body = _build_request_body(input_text)
        params = {"key": self._api_key}

        def _post() -> httpx.Response:
            if self._client is not None:
                response = self._client.post(url, params=params, json=body, timeout=self._timeout)
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, params=params, json=body)
            response.raise_for_status()
            return response

        try:
            response = execute_with_retries(
                _post,
                max_attempts=self._max_retries,
                initial_backoff_seconds=self._retry_backoff,
                provider_label="Gemini API",
            )
        except AIProviderResponseError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Gemini provider failure")
            raise AIProviderResponseError(f"Gemini analysis failed: {exc}") from exc

        payload = response.json()
        _raise_if_blocked(payload)
        raw_json = _extract_gemini_text(payload)
        return parse_and_validate_analysis_json(raw_json)

    def analyze_hybrid_reverify(
        self,
        input_text: str,
        findings: list[dict[str, object]],
    ) -> HybridReverifyResult:
        if not self._api_key.strip():
            raise AIProviderConfigError("GEMINI_API_KEY is not configured.")
        url = f"{self._base_url}/v1beta/models/{self._model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": HYBRID_REVERIFY_SYSTEM_INSTRUCTION}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": hybrid_reverify_prompt(input_text, findings)}],
                },
            ],
            "generationConfig": {
                "temperature": 0.15,
                "topP": 0.95,
                "maxOutputTokens": 1536,
                "responseMimeType": "application/json",
                "responseSchema": HYBRID_REVERIFY_RESPONSE_SCHEMA,
            },
        }
        params = {"key": self._api_key}

        def _post() -> httpx.Response:
            if self._client is not None:
                response = self._client.post(
                    url, params=params, json=body, timeout=self._timeout,
                )
            else:
                with httpx.Client(timeout=self._timeout) as client:
                    response = client.post(url, params=params, json=body)
            response.raise_for_status()
            return response

        response = execute_with_retries(
            _post,
            max_attempts=self._max_retries,
            initial_backoff_seconds=self._retry_backoff,
            provider_label="Gemini API",
        )
        payload = response.json()
        _raise_if_blocked(payload)
        return parse_and_validate_hybrid_reverify_json(_extract_gemini_text(payload))


def _build_request_body(input_text: str) -> dict[str, Any]:
    return {
        "systemInstruction": {
            "parts": [{"text": CYBERSECURITY_SYSTEM_INSTRUCTION}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": cybersecurity_analysis_prompt(input_text)}],
            },
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.95,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
            "responseSchema": CYBERSECURITY_RESPONSE_SCHEMA,
        },
    }


def _raise_if_blocked(payload: Any) -> None:
    """Surface Gemini safety / policy blocks as clear errors."""
    try:
        prompt_feedback = payload.get("promptFeedback") or {}
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            raise AIProviderResponseError(
                f"Gemini blocked the request (promptFeedback.blockReason={block_reason}).",
            )

        candidates = payload.get("candidates") or []
        if not candidates:
            raise AIProviderResponseError("Gemini returned no candidates.")

        finish_reason = candidates[0].get("finishReason")
        if finish_reason and finish_reason in _BLOCKED_FINISH_REASONS:
            raise AIProviderResponseError(
                f"Gemini blocked content generation (finishReason={finish_reason}).",
            )
    except AIProviderResponseError:
        raise
    except (AttributeError, TypeError) as exc:
        raise AIProviderResponseError("Unexpected Gemini response shape.") from exc


def _extract_gemini_text(payload: Any) -> str:
    try:
        candidates = payload["candidates"]
        parts = candidates[0]["content"]["parts"]
        texts = [p["text"] for p in parts if isinstance(p, dict) and p.get("text")]
        if not texts:
            raise KeyError("no text parts")
        return "\n".join(texts)
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderResponseError("Unexpected Gemini response shape.") from exc
