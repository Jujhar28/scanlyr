"""Synthetic / example credential fixture detection."""

from __future__ import annotations

from app.scan_security.analysis.fixtures import (
    assess_synthetic_credential_fixture,
    is_synthetic_test_email,
)
from app.scan_security.services.engine import run_security_scan


def test_synthetic_test_email() -> None:
    assert is_synthetic_test_email("test@gmail.com")
    assert is_synthetic_test_email("user@example.com")
    assert not is_synthetic_test_email("ceo@acmecorp.com")


def test_gmail_test_fixture_pair() -> None:
    text = (
        "Test user password with email test@gmail.com password is password123 for scanlyr account"
    )
    assessment = assess_synthetic_credential_fixture(text, "test@gmail.com", "password123")
    assert assessment.is_synthetic
    result = run_security_scan(text)
    assert result.risk_score <= 35, result.risk_score
    assert result.risk_level == "low"


def test_hybrid_fusion_caps_ai_for_synthetic_fixture() -> None:
    from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult
    from app.scan_security.services.engine import run_security_scan
    from app.services.scan_fusion_service import fuse_rules_and_ai

    text = (
        "Test user password with email test@gmail.com password is password123 for scanlyr account"
    )
    rules = run_security_scan(text)
    ai = ProviderAnalysisOutcome(
        result=TextAnalysisResult(
            risk_score=80,
            risk_level="high",
            explanation="Leaked credentials for unauthorized access.",
            category="secrets",
        ),
        provider_id="gemini",
        fallback_used=False,
        attempted_providers=["gemini"],
    )
    fused = fuse_rules_and_ai(rules, ai, input_text=text)
    assert fused.analysis.risk_score <= 35
    assert fused.analysis.risk_level == "low"


def test_personal_email_with_demo_password_and_scanlyr_discourse() -> None:
    text = (
        "Jujhar password with email jujhars@gmail.com password is password123 for scanlyr account"
    )
    assessment = assess_synthetic_credential_fixture(text, "jujhars@gmail.com", "password123")
    assert assessment.is_synthetic
    assert assessment.confidence >= 0.8
    result = run_security_scan(text)
    assert result.risk_score <= 35, result.risk_score
    assert result.risk_level == "low"


def test_realistic_credential_still_scores_high() -> None:
    text = "Contact jane.doe@acmecorp.com — password is Sup3rS3cret!2024xK9"
    result = run_security_scan(text)
    assert result.risk_score >= 55
