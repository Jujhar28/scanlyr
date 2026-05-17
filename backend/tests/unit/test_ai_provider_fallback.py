"""Gemini → Groq fallback provider tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.ai_providers import FallbackAIProvider, TextAnalysisResult
from app.ai_providers.errors import AIProviderConfigError, AIProviderResponseError
from app.ai_providers.factory import get_ai_provider
from app.ai_providers.gemini import GeminiProvider
from app.ai_providers.groq import GroqProvider
from app.core.config import Settings


def _result(score: int = 50) -> TextAnalysisResult:
    return TextAnalysisResult(
        risk_score=score,
        risk_level="medium",
        explanation="test",
        category="safe",
    )


def test_fallback_uses_gemini_when_successful() -> None:
    gemini = MagicMock(spec=GeminiProvider)
    gemini.analyze_text.return_value = _result(40)
    groq = MagicMock(spec=GroqProvider)

    provider = FallbackAIProvider(
        settings=_settings(),
        gemini=gemini,
        groq=groq,
    )
    out = provider.analyze_with_outcome("hello")

    assert out.provider_id == "gemini"
    assert out.fallback_used is False
    assert out.result.risk_score == 40
    groq.analyze_text.assert_not_called()


def test_fallback_switches_to_groq_on_gemini_failure() -> None:
    gemini = MagicMock(spec=GeminiProvider)
    gemini.analyze_text.side_effect = AIProviderResponseError("gemini down")
    groq = MagicMock(spec=GroqProvider)
    groq.analyze_text.return_value = _result(72)

    provider = FallbackAIProvider(settings=_settings(), gemini=gemini, groq=groq)
    out = provider.analyze_with_outcome("hello")

    assert out.provider_id == "groq"
    assert out.fallback_used is True
    assert out.attempted_providers == ["gemini", "groq"]
    assert out.result.risk_score == 72


def test_fallback_skips_gemini_without_key() -> None:
    gemini = MagicMock(spec=GeminiProvider)
    groq = MagicMock(spec=GroqProvider)
    groq.analyze_text.return_value = _result()

    provider = FallbackAIProvider(
        settings=_settings(gemini_api_key=None),
        gemini=gemini,
        groq=groq,
    )
    out = provider.analyze_with_outcome("hello")

    assert out.provider_id == "groq"
    assert out.fallback_used is False
    gemini.analyze_text.assert_not_called()


def test_fallback_raises_when_both_fail() -> None:
    gemini = MagicMock(spec=GeminiProvider)
    gemini.analyze_text.side_effect = AIProviderResponseError("gemini err")
    groq = MagicMock(spec=GroqProvider)
    groq.analyze_text.side_effect = AIProviderResponseError("groq err")

    provider = FallbackAIProvider(settings=_settings(), gemini=gemini, groq=groq)
    with pytest.raises(AIProviderResponseError, match="All configured"):
        provider.analyze_text("hello")


def test_fallback_raises_when_no_keys() -> None:
    provider = FallbackAIProvider(settings=_settings(gemini_api_key=None, groq_api_key=None))
    with pytest.raises(AIProviderConfigError, match="unavailable"):
        provider.analyze_text("hello")


def test_factory_default_is_auto_fallback() -> None:
    provider = get_ai_provider(settings=_settings())
    assert isinstance(provider, FallbackAIProvider)


def _settings(**overrides: object) -> Settings:
    base = {
        "secret_key": "unit-test-secret-key-at-least-32-chars",
        "database_url": "postgresql://postgres:postgres@localhost:5432/scanlyr",
        "gemini_api_key": "test-gemini-key",
        "groq_api_key": "test-groq-key",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]
