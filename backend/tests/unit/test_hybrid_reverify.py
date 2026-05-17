"""Hybrid AI re-verification of rule findings."""

from __future__ import annotations

from app.ai_providers.schemas import FindingAdjudicationVerdict, HybridReverifyResult
from app.scan_security.schemas.results import ExplainableRiskScore, ScanAnalysisResult
from app.scan_security.schemas.findings import SecurityFinding
from app.services.scan_ai_adjudication_service import apply_hybrid_reverify_to_rules


def _rules_with_findings() -> ScanAnalysisResult:
    findings = (
        SecurityFinding(
            type="secret_password",
            detector_id="secrets_tokens",
            category="secrets",
            risk_category="credential_exposure",
            severity="high",
            title="Password disclosed in plain language",
            description="Password value stated in plain text.",
            remediation="Rotate password.",
            confidence=0.87,
            evidence={"start": 0, "end": 10},
        ),
        SecurityFinding(
            type="sensitive_data",
            detector_id="llm_sensitive_data",
            category="pii",
            risk_category="sensitive_data_exposure",
            severity="medium",
            title="Email address",
            description="Email present.",
            remediation="Minimize PII.",
            confidence=0.72,
            evidence={"start": 20, "end": 35},
        ),
    )
    return ScanAnalysisResult(
        risk_score=75,
        risk_level="high",
        confidence=0.8,
        explanation="High risk.",
        findings=findings,
        remediation_steps=("Rotate password.",),
        content_kind="auto",
        risk_categories={"credential_exposure": 75},
        score_breakdown=ExplainableRiskScore(overall=75, categories=(), top_drivers=()),
    )


def test_apply_reverify_dismisses_false_positives() -> None:
    rules = _rules_with_findings()
    reverify = HybridReverifyResult(
        risk_score=12,
        risk_level="low",
        explanation="Example test credentials only.",
        category="test_fixture",
        finding_verdicts=[
            FindingAdjudicationVerdict(
                index=0,
                verdict="dismiss",
                reason="test@gmail.com and password123 are fixtures",
            ),
            FindingAdjudicationVerdict(
                index=1,
                verdict="dismiss",
                reason="example email",
            ),
        ],
    )
    text = "Test user password with email test@gmail.com password is password123"
    adjusted = apply_hybrid_reverify_to_rules(rules, reverify, input_text=text)
    assert len(adjusted.findings) == 0
    assert adjusted.risk_score <= 25
    assert adjusted.risk_level == "low"
