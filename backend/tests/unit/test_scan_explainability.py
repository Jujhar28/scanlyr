"""Unit tests for layered scan explainability."""

from __future__ import annotations

from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult
from app.scan_security.schemas.findings import SecurityFinding
from app.scan_security.schemas.results import ExplainableRiskScore, ScanAnalysisResult
from app.schemas.scan import ScanFusionDetails
from app.services.scan_explainability_service import build_scan_explainability, summary_text


def _finding() -> SecurityFinding:
    return SecurityFinding(
        type="secret_password",
        detector_id="password_reference",
        category="credentials",
        risk_category="sensitive_data_exposure",
        severity="high",
        title="Password reference",
        description="Text references passwords or credentials.",
        confidence=0.9,
        remediation="Remove secrets from the text.",
        evidence={},
    )


def _rules_result() -> ScanAnalysisResult:
    f = _finding()
    return ScanAnalysisResult(
        risk_score=82,
        risk_level="high",
        confidence=0.85,
        explanation="Overall high risk (score 82). Top categories: sensitive_data_exposure (82).",
        findings=(f,),
        remediation_steps=("Remove secrets.",),
        content_kind="auto",
        risk_categories={"sensitive_data_exposure": 82},
        score_breakdown=ExplainableRiskScore(
            overall=82,
            categories=(),
            top_drivers=("sensitive_data_exposure (82)",),
        ),
    )


def _ai_outcome() -> ProviderAnalysisOutcome:
    return ProviderAnalysisOutcome(
        result=TextAnalysisResult(
            risk_score=80,
            risk_level="high",
            explanation="The presence of a password suggests potential leaked credentials.",
            category="secrets",
        ),
        provider_id="groq",
        fallback_used=True,
        attempted_providers=["gemini", "groq"],
    )


def test_build_explainability_hybrid_layers() -> None:
    rules = _rules_result()
    ai = _ai_outcome()
    fusion = ScanFusionDetails(
        rules_score=82,
        ai_score=80,
        combined_score=81,
        rules_weight=0.4,
        ai_weight=0.6,
        ai_used=True,
        ai_provider="groq",
        ai_category="secrets",
    )
    fused = ScanAnalysisResult(
        risk_score=81,
        risk_level="high",
        confidence=0.8,
        explanation=rules.explanation,
        findings=rules.findings,
        remediation_steps=rules.remediation_steps,
        content_kind="auto",
        risk_categories=rules.risk_categories,
        score_breakdown=rules.score_breakdown,
    )
    exp = build_scan_explainability(
        result=fused,
        rules_result=rules,
        fusion=fusion,
        ai_outcome=ai,
        engine_version="scan_security_v4+ai",
    )
    assert "81" in exp.summary.headline
    assert exp.composition.method == "hybrid"
    assert exp.rules.primary_concerns == ["Password reference"]
    assert exp.ai.used is True
    assert exp.ai.category == "Secrets"
    assert "groq" in (exp.technical.ai_provider or "")
    assert exp.technical.ai_fallback_used is True
    assert "Combined risk score" not in summary_text(exp)
    assert len(summary_text(exp)) < 500
