"""Safety fallbacks and strict AI validation for hybrid scan."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.ai_providers._http import parse_analysis_json
from app.ai_providers.errors import AIProviderResponseError
from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult
from app.ai_providers.validation import validate_text_analysis_result
from app.core.config import Settings
from app.services.scan_ai_layer_service import try_ai_scan_analysis
from app.services.scan_safety_service import (
    SAFE_ENGINE_VERSION,
    build_safe_default_scan_result,
    run_hybrid_scan_analysis,
    try_rules_scan,
)


def _settings(**overrides: object) -> Settings:
    base = {
        "secret_key": "unit-test-secret-key-at-least-32-chars",
        "database_url": "postgresql://postgres:postgres@localhost:5432/scanlyr",
        "gemini_api_key": "test-gemini-key",
        "groq_api_key": "test-groq-key",
        "scan_ai_fusion_enabled": True,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_parse_analysis_json_rejects_extra_fields() -> None:
    payload = {
        "risk_score": 50,
        "risk_level": "medium",
        "explanation": "test",
        "category": "test",
        "unexpected": True,
    }
    with pytest.raises(AIProviderResponseError, match="Unexpected JSON fields"):
        parse_analysis_json(json.dumps(payload))


def test_validate_coerces_mismatched_risk_level() -> None:
    raw = TextAnalysisResult(
        risk_score=85,
        risk_level="low",
        explanation="High risk content detected.",
        category="secrets",
    )
    fixed = validate_text_analysis_result(raw)
    assert fixed.risk_level == "high"
    assert fixed.risk_score == 85


def test_try_ai_scan_analysis_rejects_malformed_outcome() -> None:
    with patch("app.services.scan_ai_layer_service.get_ai_provider") as mock_get:
        mock_provider = mock_get.return_value
        mock_provider.provider_id = "gemini"
        mock_provider.analyze_text.return_value = TextAnalysisResult(
            risk_score=50,
            risk_level="medium",
            explanation="valid explanation",
            category="!!!",
        )
        outcome = try_ai_scan_analysis("test input", settings=_settings())
    assert outcome is None


def test_run_hybrid_scan_safe_default_when_rules_fail() -> None:
    safe = build_safe_default_scan_result("auto")
    result, fusion, engine = run_hybrid_scan_analysis(
        "anything",
        content_type="auto",
        settings=_settings(),
        ai_outcome=None,
        rules_result=None,
    )
    assert result.risk_score == safe.risk_score
    assert result.risk_level == "low"
    assert fusion.ai_used is False
    assert engine == SAFE_ENGINE_VERSION


def test_try_rules_scan_returns_none_on_engine_error() -> None:
    with patch(
        "app.services.scan_safety_service.analyze_security_text",
        side_effect=RuntimeError("engine down"),
    ):
        assert try_rules_scan("text") is None
