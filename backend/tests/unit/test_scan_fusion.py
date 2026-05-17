"""Unit tests for rules + AI score fusion."""

from __future__ import annotations

from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult
from app.scan_security.schemas.results import ExplainableRiskScore, ScanAnalysisResult
from app.services.scan_fusion_service import fuse_rules_and_ai


def _rules_result(score: int, *, explanation: str = "Rules found issues.") -> ScanAnalysisResult:
    return ScanAnalysisResult(
        risk_score=score,
        risk_level="high" if score >= 80 else "medium" if score >= 40 else "low",
        confidence=0.85,
        explanation=explanation,
        findings=(),
        remediation_steps=("Rotate credentials.",),
        content_kind="auto",
        risk_categories={"credential_exposure": score},
        score_breakdown=ExplainableRiskScore(overall=score, categories=(), top_drivers=()),
    )


def _ai_outcome(score: int, *, category: str = "data_exfiltration") -> ProviderAnalysisOutcome:
    level = "high" if score >= 80 else "medium" if score >= 40 else "low"
    return ProviderAnalysisOutcome(
        result=TextAnalysisResult(
            risk_score=score,
            risk_level=level,
            explanation="AI detected suspicious patterns.",
            category=category,
        ),
        provider_id="gemini",
        fallback_used=False,
        attempted_providers=["gemini"],
    )


def test_fusion_rules_only_when_ai_missing() -> None:
    rules = _rules_result(82)
    fused = fuse_rules_and_ai(rules, None)
    assert fused.analysis.risk_score == 82
    assert fused.fusion.ai_used is False
    assert fused.fusion.ai_score is None
    assert fused.fusion.combined_score == 82


def test_fusion_weighted_combined_score() -> None:
    rules = _rules_result(80)
    ai = _ai_outcome(50)
    fused = fuse_rules_and_ai(rules, ai, rules_weight=0.4, ai_weight=0.6)
    # 0.4*80 + 0.6*50 = 32 + 30 = 62
    assert fused.analysis.risk_score == 62
    assert fused.fusion.rules_score == 80
    assert fused.fusion.ai_score == 50
    assert fused.fusion.ai_used is True
    assert fused.fusion.ai_provider == "gemini"


def test_fusion_merges_remediation() -> None:
    rules = _rules_result(90, explanation="Critical credential leak.")
    ai = _ai_outcome(70, category="credential_exposure")
    fused = fuse_rules_and_ai(rules, ai)
    assert fused.analysis.explanation == "Critical credential leak."
    assert len(fused.analysis.remediation_steps) >= 2
