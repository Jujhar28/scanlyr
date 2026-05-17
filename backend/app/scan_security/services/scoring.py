from __future__ import annotations

from collections import defaultdict

from app.scan_security.analysis.context import TextContextProfile
from app.scan_security.context import ContentKind, RiskCategory
from app.scan_security.schemas.findings import SecurityFinding, Severity
from app.scan_security.schemas.results import (
    CategoryScore,
    ExplainableRiskScore,
    RiskLevel,
    ScanAnalysisResult,
)

_SEVERITY_BASE: dict[Severity, int] = {
    "critical": 90,
    "high": 82,
    "medium": 52,
    "low": 22,
}

_SEVERITY_BONUS: dict[Severity, int] = {
    "critical": 8,
    "high": 6,
    "medium": 4,
    "low": 2,
}


def risk_level_from_score(score: int, findings: list[SecurityFinding] | None = None) -> RiskLevel:
    has_critical = bool(findings) and any(f.severity == "critical" for f in findings)
    if score >= 90 or (score >= 80 and has_critical):
        return "critical"
    if score >= 80:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def compute_risk_score(findings: list[SecurityFinding]) -> int:
    """Confidence-weighted score with diminishing returns for many findings."""
    if not findings:
        return 8
    weighted = sorted(
        (_SEVERITY_BASE[f.severity] * max(0.35, f.confidence) for f in findings),
        reverse=True,
    )
    primary = weighted[0]
    secondary = sum(weighted[1:]) * 0.28 if len(weighted) > 1 else 0.0
    return min(100, max(8, int(round(primary + min(16, secondary)))))


def apply_context_dampening(score: int, profile: TextContextProfile | None) -> int:
    if profile is None:
        return score
    dampened = int(round(score * profile.risk_dampening))
    return max(0, min(100, dampened))


def compute_confidence(findings: list[SecurityFinding], risk_score: int) -> float:
    if not findings:
        return 0.55
    detector_count = len({f.detector_id for f in findings})
    avg_finding_conf = sum(f.confidence for f in findings) / len(findings)
    raw = (
        0.35 * avg_finding_conf
        + 0.08 * min(6, len(findings))
        + 0.04 * min(4, detector_count)
        + risk_score / 300.0
    )
    return round(min(0.99, raw), 3)


def _category_score(findings: list[SecurityFinding], category: RiskCategory) -> int:
    cat_findings = [f for f in findings if f.risk_category == category]
    if not cat_findings:
        return 0
    return compute_risk_score(cat_findings)


def build_explainable_score(findings: list[SecurityFinding], overall: int) -> ExplainableRiskScore:
    by_cat: dict[RiskCategory, list[SecurityFinding]] = defaultdict(list)
    for f in findings:
        by_cat[f.risk_category].append(f)  # type: ignore[arg-type]

    categories: list[CategoryScore] = []
    for cat in sorted(by_cat.keys()):
        cat_findings = by_cat[cat]
        score = _category_score(cat_findings, cat)
        top = sorted(cat_findings, key=lambda x: _SEVERITY_BASE[x.severity], reverse=True)[:2]
        titles = ", ".join(t.title for t in top)
        explanation = (
            f"{len(cat_findings)} finding(s) in '{cat}' (score {score}). "
            f"Primary signals: {titles}."
            if top
            else f"No active findings in '{cat}'."
        )
        categories.append(
            CategoryScore(
                risk_category=cat,
                score=score,
                finding_count=len(cat_findings),
                explanation=explanation,
            ),
        )

    categories.sort(key=lambda c: c.score, reverse=True)
    top_drivers = tuple(f"{c.risk_category} ({c.score})" for c in categories[:5] if c.score > 0)
    return ExplainableRiskScore(overall=overall, categories=tuple(categories), top_drivers=top_drivers)


def build_explanation(
    findings: list[SecurityFinding],
    risk_level: RiskLevel,
    breakdown: ExplainableRiskScore,
) -> str:
    if not findings:
        return (
            "No high-confidence security issues detected. Content passed pattern checks "
            "for credentials, injection, and sensitive data exposure."
        )
    ordered = sorted(
        findings,
        key=lambda f: _SEVERITY_BASE[f.severity] * f.confidence,
        reverse=True,
    )
    top = ordered[:3]
    parts = [f.title for f in top]
    summary = ", ".join(parts)
    if len(findings) > 3:
        summary += f", plus {len(findings) - 3} more"
    drivers = ", ".join(breakdown.top_drivers[:3]) if breakdown.top_drivers else "none"
    return (
        f"{risk_level.title()} risk (score {breakdown.overall}). "
        f"Primary concerns: {summary}. Top categories: {drivers}."
    )


def aggregate_findings(
    findings: list[SecurityFinding],
    *,
    content_kind: ContentKind = "auto",
    context_profile: TextContextProfile | None = None,
) -> ScanAnalysisResult:
    raw_score = compute_risk_score(findings)
    risk_score = apply_context_dampening(raw_score, context_profile)
    risk_level = risk_level_from_score(risk_score, findings)
    confidence = compute_confidence(findings, risk_score)
    breakdown = build_explainable_score(findings, risk_score)
    explanation = build_explanation(findings, risk_level, breakdown)
    remediation_steps = tuple(dict.fromkeys(f.remediation for f in findings))
    risk_categories = {c.risk_category: c.score for c in breakdown.categories if c.score > 0}
    return ScanAnalysisResult(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=confidence,
        explanation=explanation,
        findings=tuple(findings),
        remediation_steps=remediation_steps,
        content_kind=content_kind,
        risk_categories=risk_categories,
        score_breakdown=breakdown,
    )
