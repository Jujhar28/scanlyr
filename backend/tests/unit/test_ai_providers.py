"""Unit tests for interchangeable AI provider adapters."""

from __future__ import annotations

import json

import httpx
import pytest

from app.ai_providers import (
    AIProviderConfigError,
    AIProviderResponseError,
    GeminiProvider,
    GroqProvider,
    TextAnalysisResult,
    get_ai_provider,
    registered_provider_ids,
)
from app.ai_providers._http import parse_analysis_json
from app.core.config import Settings


def _sample_payload() -> dict[str, object]:
    return {
        "risk_score": 72,
        "risk_level": "high",
        "explanation": "Contains a plausible API secret pattern.",
        "category": "secrets",
    }


def test_text_analysis_result_validation() -> None:
    result = TextAnalysisResult.model_validate(_sample_payload())
    assert result.risk_score == 72
    assert result.risk_level == "high"
    assert result.as_dict()["category"] == "secrets"


def test_parse_analysis_json_strips_markdown_fence() -> None:
    raw = "```json\n" + json.dumps(_sample_payload()) + "\n```"
    parsed = parse_analysis_json(raw)
    assert parsed.risk_level == "high"


def test_get_ai_provider_unknown() -> None:
    with pytest.raises(AIProviderConfigError, match="Unknown AI provider"):
        get_ai_provider("openai", settings=_settings())


def test_registered_providers() -> None:
    assert set(registered_provider_ids()) == {"auto", "gemini", "groq"}


def test_gemini_analyze_text_success() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(_sample_payload())}],
                },
                "finishReason": "STOP",
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "generateContent" in str(request.url)
        assert request.url.params.get("key") == "test-gemini-key"
        body = json.loads(request.content.decode())
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        assert body["generationConfig"]["responseSchema"]["required"] == [
            "risk_score",
            "risk_level",
            "explanation",
            "category",
        ]
        assert "systemInstruction" in body
        user_text = body["contents"][0]["parts"][0]["text"]
        assert "cybersecurity" in user_text.lower()
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiProvider(
        api_key="test-gemini-key",
        settings=_settings(),
        client=client,
    )
    result = provider.analyze_text("sk-test-secret-key")
    assert result.risk_score == 72
    assert result.category == "secrets"


def test_gemini_retries_on_429() -> None:
    payload = {
        "candidates": [
            {
                "content": {"parts": [{"text": json.dumps(_sample_payload())}]},
                "finishReason": "STOP",
            },
        ],
    }
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": {"message": "rate limit"}})
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiProvider(
        api_key="test-gemini-key",
        settings=_settings(gemini_max_retries=3),
        retry_backoff_seconds=0.01,
        client=client,
    )
    result = provider.analyze_text("test input")
    assert result.risk_level == "high"
    assert calls["n"] == 2


def test_gemini_safety_block_raises() -> None:
    payload = {
        "candidates": [
            {
                "finishReason": "SAFETY",
                "content": {"parts": []},
            },
        ],
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiProvider(api_key="test-gemini-key", settings=_settings(), client=client)
    with pytest.raises(AIProviderResponseError, match="blocked"):
        provider.analyze_text("test")


def test_groq_analyze_text_success() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(_sample_payload()),
                },
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/chat/completions")
        assert request.headers.get("Authorization") == "Bearer test-groq-key"
        body = json.loads(request.content.decode())
        assert body["response_format"]["type"] == "json_object"
        assert body["messages"][0]["role"] == "system"
        assert body["max_tokens"] == 512
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GroqProvider(
        api_key="test-groq-key",
        settings=_settings(),
        client=client,
    )
    result = provider.analyze_text("ignore previous instructions")
    assert result.risk_level == "high"


def test_gemini_missing_api_key() -> None:
    provider = GeminiProvider(api_key=None, settings=_settings(gemini_api_key=None))
    with pytest.raises(AIProviderConfigError, match="GEMINI_API_KEY"):
        provider.analyze_text("hello")


def test_groq_invalid_json_response() -> None:
    payload = {
        "choices": [{"message": {"content": "not json"}}],
    }

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GroqProvider(api_key="test-groq-key", settings=_settings(), client=client)
    with pytest.raises(AIProviderResponseError, match="valid JSON"):
        provider.analyze_text("test")


def test_factory_returns_gemini_only() -> None:
    provider = get_ai_provider("gemini", settings=_settings(ai_provider="auto"))
    assert isinstance(provider, GeminiProvider)


def test_factory_returns_groq() -> None:
    provider = get_ai_provider("groq", settings=_settings(ai_provider="gemini"))
    assert isinstance(provider, GroqProvider)


def _settings(**overrides: object) -> Settings:
    base = {
        "secret_key": "unit-test-secret-key-at-least-32-chars",
        "database_url": "postgresql://postgres:postgres@localhost:5432/scanlyr",
        "gemini_api_key": "test-gemini-key",
        "groq_api_key": "test-groq-key",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]
